from pathlib import Path
from urllib.parse import urlparse
from dataclasses import dataclass
import tempfile
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Union, Dict, Any
import re

import httpx
import rich.progress
from retrying import retry  # type: ignore

from capella_console_client.logconf import logger
from capella_console_client.hooks import (
    retry_if_httpx_status_error,
    log_attempt_delay,
)
from capella_console_client.exceptions import ConnectError


STAC_ID_REGEX = re.compile("^.*(CAPELLA_\\w+_\\w+_\\w+_\\d{14}_\\d{14}).*$")
PRODUCT_TYPE_REGEX = re.compile("^.*CAPELLA_\\w+_\\w+_(\\w+)_\\w+_\\d{14}_\\d{14}.*$")


@dataclass
class DownloadRequest:
    url: str
    local_path: Path
    asset_key: str
    stac_id: str = ""


progress_bar = rich.progress.Progress(
    rich.progress.TextColumn("[bold blue]{task.fields[filename]}", justify="left"),
    rich.progress.BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    rich.progress.DownloadColumn(),
    "•",
    rich.progress.TransferSpeedColumn(),
    "•",
    rich.progress.TimeRemainingColumn(),
)


def _flush_progress_bar(progress: rich.progress.Progress) -> None:
    for task_id in progress.task_ids:
        progress.remove_task(task_id)


def _gather_download_requests(
    assets_presigned: Dict[str, Any],
    local_dir: Union[Path, str] = Path(tempfile.gettempdir()),
    include: Union[List[str], str] = None,
    exclude: Union[List[str], str] = None,
    separate_dirs: bool = True,
) -> List[DownloadRequest]:
    local_dir = Path(local_dir)
    assert local_dir.exists(), f"{local_dir} does not exist"

    stac_id = _derive_stac_id(assets_presigned)

    if separate_dirs:
        local_dir /= stac_id
        local_dir.mkdir(exist_ok=True)

    logger.info(f"downloading product {stac_id} to {local_dir}")

    if include:
        include = _prep_include_exclude(include)
        logger.info(f"Only including assets {', '.join(include)}")

    if exclude:
        exclude = _prep_include_exclude(exclude)
        logger.info(f"Excluding assets {', '.join(exclude)}")

    # gather up paths
    download_requests = []
    for key, asset in assets_presigned.items():
        # white-listing asset
        if include and key not in include:
            continue

        # black-listing asset
        if exclude and key in exclude:
            continue

        local_path = local_dir / _get_filename(asset["href"])
        download_requests.append(
            DownloadRequest(
                stac_id=stac_id,
                asset_key=key,
                url=asset["href"],
                local_path=local_path,
            )
        )
    return download_requests


def _get_raster_href(assets_presigned: Dict[str, Any]) -> str:
    raster_asset = assets_presigned.get("HH")
    if raster_asset is None:
        raster_asset = assets_presigned["VV"]

    raster_asset_href: str = raster_asset["href"]
    return raster_asset_href


def _derive_stac_id(assets_presigned: Dict[str, Any]) -> str:
    raster_asset_href = _get_raster_href(assets_presigned)
    try:
        stac_id: str = STAC_ID_REGEX.findall(raster_asset_href)[0]
    except IndexError:
        raise ValueError(f"Could not derive STAC ID from {raster_asset_href}")
    return stac_id


def _derive_product_type(assets_presigned: Dict[str, Any]) -> str:
    raster_asset_href = _get_raster_href(assets_presigned)
    try:
        product_type: str = PRODUCT_TYPE_REGEX.findall(raster_asset_href)[0]
    except IndexError:
        raise ValueError(f"Could not derive product type from {raster_asset_href}")
    return product_type


def _filter_assets_by_product_types(
    assets_presigned: List[Dict[str, Any]], product_types: List[str]
) -> List[Dict[str, Any]]:
    logger.info(f'filtering by product_types: {", ".join(product_types)}')
    filtered_assets = []
    for cur_assets in assets_presigned:
        cur_product_type = _derive_product_type(cur_assets)
        if cur_product_type in product_types:
            filtered_assets.append(cur_assets)

    return filtered_assets


def _prep_include_exclude(filter_stmnt: Union[str, List[str]]) -> List[str]:
    if isinstance(filter_stmnt, str):
        filter_stmnt = [filter_stmnt]

    if "raster" in filter_stmnt:
        filter_stmnt.extend(["HH", "VV"])
        filter_stmnt.pop(filter_stmnt.index("raster"))

    return list(set(filter_stmnt))


def _perform_download(
    download_requests: List[DownloadRequest],
    override: bool,
    threaded: bool,
    show_progress: bool = False,
) -> Dict[str, Path]:

    local_paths_by_key = {}

    with progress_bar as progress:
        _flush_progress_bar(progress)

        # serially
        if not threaded:
            for dl_request in download_requests:
                local_paths_by_key[dl_request.asset_key] = _download_asset(
                    dl_request,
                    override=override,
                    show_progress=show_progress,
                    progress=progress,
                )

        # threaded
        else:
            with ThreadPoolExecutor(max_workers=len(download_requests)) as executor:
                # Start the load operations and mark each future with its URL
                futures_by_key = {}

                for dl_request in download_requests:
                    futures_by_key[dl_request.asset_key] = executor.submit(
                        _download_asset,
                        dl_request=dl_request,
                        override=override,
                        show_progress=show_progress,
                        progress=progress,
                    )

            for key, fut in futures_by_key.items():
                local_paths_by_key[key] = fut.result()

    return local_paths_by_key


def _download_asset(
    dl_request: DownloadRequest,
    override: bool,
    show_progress: bool,
    progress: rich.progress.Progress,
) -> Path:
    if dl_request.local_path is None:
        local_file = _get_filename(dl_request.url)
        dl_request.local_path = Path(tempfile.gettempdir()) / local_file

    dl_request.local_path = Path(dl_request.local_path)

    if not override and dl_request.local_path.exists():
        logger.info(f"already downloaded to {dl_request.local_path}")
        return dl_request.local_path

    try:
        asset_size = _get_asset_bytesize(dl_request.url)
    except Exception:
        asset_size = -1

    if not show_progress:
        size_suffix = f"({_sizeof_fmt(asset_size)})" if asset_size != -1 else ""
        logger.info(f"downloading to {dl_request.local_path} {size_suffix}")

    _fetch(dl_request, asset_size, show_progress, progress)

    if not show_progress:
        logger.info(f"successfully downloaded to {dl_request.local_path}")

    return dl_request.local_path


@retry(
    retry_on_exception=retry_if_httpx_status_error,
    wait_func=log_attempt_delay,
    wait_exponential_multiplier=2000,
    wait_exponential_max=16000,
)
def _fetch(
    dl_request: DownloadRequest,
    asset_size: int,
    show_progress: bool,
    progress: rich.progress.Progress,
):
    try:
        with open(dl_request.local_path, "wb") as f:
            with httpx.stream("GET", dl_request.url) as response:
                response.raise_for_status()
                if show_progress:
                    download_task_id = _register_progress_task(
                        dl_request, progress, asset_size
                    )

                for chunk in response.iter_bytes():
                    f.write(chunk)

                    if show_progress:
                        progress.update(
                            download_task_id, completed=response.num_bytes_downloaded
                        )
    except httpx.ConnectError as e:
        raise ConnectError(f"Could not connect to {dl_request.url}: {e}") from None

    return dl_request.local_path


def _register_progress_task(
    dl_request: DownloadRequest, progress: rich.progress.Progress, asset_size: int
) -> rich.progress.TaskID:
    file_name_str = str(dl_request.local_path)
    if dl_request.local_path and isinstance(dl_request.local_path, Path):
        file_name_str = dl_request.local_path.name
    download_task_id = progress.add_task(
        "Download", total=asset_size, filename=file_name_str
    )
    return download_task_id


def _get_filename(pre_signed_url: str) -> str:
    return Path(urlparse(pre_signed_url).path).name


def _get_asset_bytesize(pre_signed_url: str) -> int:
    """get size in bytes of `pre_signed_url`"""
    try:
        with httpx.stream("GET", pre_signed_url) as resp:
            total_size = int(resp.headers["Content-Length"])
    except httpx.ConnectError as e:
        raise ConnectError(f"Could not connect to {pre_signed_url}: {e}") from None
    return total_size


def _sizeof_fmt(num, suffix="B"):
    for unit in ["", "Ki", "Mi", "Gi", "Ti", "Pi", "Ei", "Zi"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f} {unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f} Yi{suffix}"
