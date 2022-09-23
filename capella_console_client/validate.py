import uuid
import re
from collections import Counter

from typing import no_type_check, Optional, List, Dict, Any, Union

from capella_console_client.enumerations import ProductType, AssetType
from capella_console_client.logconf import logger
from capella_console_client.search import SearchResult

STAC_ID_REGEX_STRICT = re.compile("^CAPELLA_C\\d{2}_\\w+_\\w+_\\w{2}_\\d{14}_\\d{14}$")


@no_type_check
def _validate_uuid(uuid_str: str) -> None:
    try:
        uuid.UUID(uuid_str)
    except ValueError as e:
        raise ValueError(f"{uuid_str} is not a valid uuid: {e}")


def _validate_stac_id_or_stac_items(
    stac_ids: Optional[List[str]] = None,
    items: Union[Optional[List[Dict[str, Any]]], SearchResult] = None,
) -> List[str]:
    if not stac_ids and not items:
        raise ValueError("Please provide stac_ids or items")

    if not stac_ids:
        stac_ids = [f["id"] for f in items]  # type: ignore

    return stac_ids


def _validate_and_filter_product_types(
    product_types: Optional[List[str]],
) -> Optional[List[str]]:
    if not product_types:
        return None
    return [p.upper() for p in product_types if p.upper() in ProductType]


def _validate_and_filter_asset_types(
    asset_types: Union[List[str], str, None],
) -> Optional[List[str]]:
    if not asset_types:
        return None
    if isinstance(asset_types, str):
        return [a for a in [asset_types] if a in AssetType]
    return [a for a in asset_types if a in AssetType]


def _validate_and_filter_stac_ids(stac_ids: Optional[List[str]]) -> List[str]:
    if not stac_ids:
        return []

    valid_stac_ids = list(set(filter(STAC_ID_REGEX_STRICT.match, stac_ids)))

    diff = set(stac_ids) - set(valid_stac_ids)
    if diff:
        logger.warning(f"filtered {','.join(diff)} (no valid STAC id)")

    if not valid_stac_ids:
        logger.warning("No valid STAC id provided")
        return []

    duplicates = [k for k, v in Counter(stac_ids).items() if v > 1]
    if duplicates:
        logger.warning(f"filtered {','.join(duplicates)} (duplicate)")

    return valid_stac_ids
