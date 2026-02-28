from typing import Any
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor

import geojson
from dateutil.parser import parse

from capella_console_client.session import CapellaConsoleSession
from capella_console_client.validate import (
    _snake_to_camel,
    _datetime_to_iso8601_str,
    _set_squint_default,
)
from capella_console_client.config import (
    TASKING_REQUEST_COLLECT_CONSTRAINTS_FIELDS,
    TR_CANCEL_MAX_CONCURRENCY,
)
from capella_console_client.enumerations import (
    ObservationDirection,
    OrbitState,
    ProductType,
    OrbitalPlane,
    CollectionTier,
    Polarization,
    ArchiveHoldback,
    LocalTimeOption,
    SquintMode,
    CollectionType,
)
from capella_console_client.exceptions import CapellaConsoleClientError


def create_tasking_request(
    session: CapellaConsoleSession,
    geometry: geojson.geometry.Geometry,
    name: str,
    description: str | None = "",
    collection_type: CollectionType | str | None = CollectionType.SPOTLIGHT,
    collection_tier: CollectionTier | str | None = CollectionTier.standard,
    window_open: datetime | str | None = None,
    window_close: datetime | str | None = None,
    local_time: LocalTimeOption | list[int] | None = None,
    product_types: list[ProductType | str] | None = None,
    off_nadir_min: int | None = None,
    off_nadir_max: int | None = None,
    image_width: int | None = None,
    orbital_planes: list[OrbitalPlane | int] | None = None,
    asc_dsc: OrbitState | str | None = OrbitState.either,
    look_direction: ObservationDirection | str | None = ObservationDirection.either,
    polarization: Polarization | str | None = None,
    archive_holdback: ArchiveHoldback | str | None = ArchiveHoldback.none,
    custom_attribute_1: str | None = None,
    custom_attribute_2: str | None = None,
    pre_approval: bool = False,
    azimuth_angle_min: int | None = None,
    azimuth_angle_max: int | None = None,
    squint: SquintMode | str | None = None,
    max_squint_angle: int | None = None,
    contract_id: str | None = None,
) -> dict[str, Any]:

    window_open, window_close = _set_window_open_close(window_open, window_close)

    if squint is None:
        squint = _set_squint_default(geometry)

    loc = locals()
    collect_constraints = {
        _snake_to_camel(k): loc[k]
        for k in TASKING_REQUEST_COLLECT_CONSTRAINTS_FIELDS
        if k in loc and loc[k] is not None
    }

    payload = {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "taskingrequestName": name,
            "taskingrequestDescription": description,
            "windowOpen": window_open,
            "windowClose": window_close,
            "collectionTier": collection_tier,
            "collectionType": collection_type,
            "archiveHoldback": archive_holdback,
            "customAttribute1": custom_attribute_1,
            "customAttribute2": custom_attribute_2,
            "pre_approval": pre_approval,
            "collectConstraints": collect_constraints,
        },
    }

    if product_types is not None:
        payload["properties"]["processingConfig"] = {"productTypes": product_types}

    if contract_id:
        payload["contractId"] = contract_id

    return session.post("/task", json=payload).json()


def _set_window_open_close(window_open: datetime | str | None, window_close: datetime | str | None) -> tuple[str, str]:
    # Normalize window_open to datetime
    if window_open is None:
        window_open_dt = datetime.now(timezone.utc)
    elif isinstance(window_open, str):
        window_open_dt = parse(window_open)
    else:
        window_open_dt = window_open

    # Normalize window_close to datetime
    if window_close is None:
        window_close_dt = window_open_dt + timedelta(days=7)
    elif isinstance(window_close, str):
        window_close_dt = parse(window_close)
    else:
        window_close_dt = window_close

    # Convert to ISO8601 strings
    return (_datetime_to_iso8601_str(window_open_dt), _datetime_to_iso8601_str(window_close_dt))


def get_tasking_request(tasking_request_id: str, session: CapellaConsoleSession) -> dict[str, Any]:
    task_response = session.get(f"/task/{tasking_request_id}")
    return task_response.json()


def _task_contains_status(task: dict[str, Any], status_name: str) -> bool:
    return status_name.lower() in (s["code"] for s in task["properties"]["statusHistory"])


def cancel_tasking_requests(
    *tasking_request_ids: str,
    session: CapellaConsoleSession,
) -> dict[str, Any]:
    return _cancel_multi_parallel(*tasking_request_ids, session=session, cancel_fct=_cancel_tasking_request)


def _cancel_multi_parallel(*cancel_ids: str, session, cancel_fct):
    max_workers = min(TR_CANCEL_MAX_CONCURRENCY, len(cancel_ids))

    results_by_cancel_id = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures_by_cancel_id = {}

        for _id in cancel_ids:
            futures_by_cancel_id[_id] = executor.submit(
                cancel_fct,
                session=session,
                cancel_id=_id,
            )

        for key, fut in futures_by_cancel_id.items():
            results_by_cancel_id[key] = fut.result()

    return results_by_cancel_id


def _cancel_tasking_request(session: CapellaConsoleSession, cancel_id: str):
    return _cancel_worker(session=session, endpoint=f"task/{cancel_id}/status")


def _cancel_worker(session: CapellaConsoleSession, endpoint: str):
    try:
        session.patch(endpoint, json={"status": "canceled"})
    except CapellaConsoleClientError as exc:
        if exc.response is not None:
            return {"success": False, **exc.response.json()}
        return {"success": False}

    return {
        "success": True,
    }
