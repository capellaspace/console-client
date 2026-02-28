from typing import Any
from datetime import datetime, timezone

import geojson

from capella_console_client.session import CapellaConsoleSession
from capella_console_client.exceptions import RepeatRequestPayloadValidationError, ContractNotFoundError
from capella_console_client.validate import _snake_to_camel, _datetime_to_iso8601_str, _set_squint_default
from capella_console_client.config import (
    REPEAT_REQUEST_COLLECT_CONSTRAINTS_FIELDS,
    REPEAT_REQUESTS_REPETITION_PROPERTIES_FIELDS,
)
from capella_console_client.enumerations import (
    ObservationDirection,
    OrbitState,
    ProductType,
    OrbitalPlane,
    RepeatCollectionTier,
    Polarization,
    ArchiveHoldback,
    LocalTimeOption,
    CollectionType,
    SquintMode,
    RepeatCycle,
)
from capella_console_client.tasking_request import _cancel_multi_parallel, _cancel_worker


def create_repeat_request(
    session: CapellaConsoleSession,
    geometry: geojson.geometry.Geometry,
    name: str,
    description: str | None = "",
    collection_type: CollectionType | str | None = CollectionType.SPOTLIGHT,
    collection_tier: str | RepeatCollectionTier | None = RepeatCollectionTier.routine,
    repeat_start: datetime | str | None = None,
    repeat_end: datetime | str | None = None,
    repetition_interval: RepeatCycle | int | None = RepeatCycle.WEEKLY,
    repetition_count: int | None = None,
    local_time: LocalTimeOption | list[int] | None = None,
    product_types: list[ProductType | str] | None = None,
    off_nadir_min: int | None = None,
    off_nadir_max: int | None = None,
    image_width: int | None = None,
    orbital_planes: list[OrbitalPlane | int] | None = None,
    asc_dsc: OrbitState | str | None = OrbitState.either,
    look_direction: ObservationDirection | str | None = ObservationDirection.either,
    polarization: Polarization | str | None = None,
    archive_holdback: str | ArchiveHoldback | None = ArchiveHoldback.none,
    custom_attribute_1: str | None = None,
    custom_attribute_2: str | None = None,
    azimuth_angle_min: int | None = None,
    azimuth_angle_max: int | None = None,
    squint: SquintMode | str | None = None,
    max_squint_angle: int | None = None,
    contract_id: str | None = None,
) -> dict[str, Any]:
    repeat_start, repeat_end = _set_repetition_start_end(repeat_start, repeat_end, repetition_count)

    if squint is None:
        squint = _set_squint_default(geometry)

    loc = locals()
    collect_constraints = {
        _snake_to_camel(k): loc[k] for k in REPEAT_REQUEST_COLLECT_CONSTRAINTS_FIELDS if k in loc and loc[k] is not None
    }
    repetition_properties = {
        _snake_to_camel(k): loc[k]
        for k in REPEAT_REQUESTS_REPETITION_PROPERTIES_FIELDS
        if k in loc and loc[k] is not None
    }

    payload = {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "repeatrequestName": name,
            "repeatrequestDescription": description,
            "collectionTier": collection_tier,
            "collectionType": collection_type,
            "archiveHoldback": archive_holdback,
            "customAttribute1": custom_attribute_1,
            "customAttribute2": custom_attribute_2,
            "collectConstraints": collect_constraints,
            "repetitionProperties": repetition_properties,
        },
    }

    if product_types is not None:
        payload["properties"]["processingConfig"] = {"productTypes": product_types}

    if contract_id:
        payload["contractId"] = contract_id

    return session.post("/repeat-requests", json=payload).json()


def _set_repetition_start_end(
    repeat_start: datetime | str | None,
    repeat_end: datetime | str | None,
    repetition_count: int | None,
) -> tuple[str, str | None]:
    if repeat_end is not None and repetition_count is not None:
        raise RepeatRequestPayloadValidationError(
            "Only one of 'repeat_end' and 'repetition_count' can be defined. Please remove one of those values from your request and try again."
        )

    if repeat_start is None:
        repeat_start = datetime.now(timezone.utc)

    repeat_start = _datetime_to_iso8601_str(repeat_start)

    if repeat_end is not None:
        repeat_end = _datetime_to_iso8601_str(repeat_end)

    return (repeat_start, repeat_end)


def cancel_repeat_requests(
    *repeat_request_ids: str,
    session: CapellaConsoleSession,
) -> dict[str, Any]:
    return _cancel_multi_parallel(*repeat_request_ids, session=session, cancel_fct=_cancel_repeat_request)


def _cancel_repeat_request(session: CapellaConsoleSession, cancel_id: str):
    return _cancel_worker(session=session, endpoint=f"repeat-requests/{cancel_id}/status")
