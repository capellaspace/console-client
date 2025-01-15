from typing import Optional, Dict, Any, List, Union, Tuple
from datetime import datetime

import geojson

from capella_console_client.session import CapellaConsoleSession
from capella_console_client.exceptions import RepeatRequestPayloadValidationError
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


def create_repeat_request(
    session: CapellaConsoleSession,
    geometry: geojson.geometry.Geometry,
    name: str,
    description: Optional[str] = "",
    collection_type: Optional[Union[CollectionType, str]] = CollectionType.SPOTLIGHT,
    collection_tier: Optional[Union[str, RepeatCollectionTier]] = RepeatCollectionTier.routine,
    repeat_start: Optional[Union[datetime, str]] = None,
    repeat_end: Optional[Union[datetime, str]] = None,
    repetition_interval: Optional[Union[RepeatCycle, int]] = RepeatCycle.WEEKLY,
    repetition_count: Optional[int] = None,
    local_time: Optional[Union[LocalTimeOption, List[int]]] = None,
    product_types: Optional[List[Union[ProductType, str]]] = None,
    off_nadir_min: Optional[int] = None,
    off_nadir_max: Optional[int] = None,
    image_width: Optional[int] = None,
    orbital_planes: Optional[List[Union[OrbitalPlane, int]]] = None,
    asc_dsc: Optional[Union[OrbitState, str]] = OrbitState.either,
    look_direction: Optional[Union[ObservationDirection, str]] = ObservationDirection.either,
    polarization: Optional[Union[Polarization, str]] = None,
    archive_holdback: Optional[Union[str, ArchiveHoldback]] = ArchiveHoldback.none,
    custom_attribute_1: Optional[str] = None,
    custom_attribute_2: Optional[str] = None,
    azimuth_angle_min: Optional[int] = None,
    azimuth_angle_max: Optional[int] = None,
    squint: Optional[Union[SquintMode, str]] = None,
    max_squint_angle: Optional[int] = None,
) -> Dict[str, Any]:
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

    return session.post("/repeat-requests", json=payload).json()


def _set_repetition_start_end(
    repeat_start: Optional[Union[datetime, str]],
    repeat_end: Optional[Union[datetime, str]],
    repetition_count: Optional[int],
) -> Tuple[str, Optional[str]]:
    if repeat_end is not None and repetition_count is not None:
        raise RepeatRequestPayloadValidationError(
            "Only one of 'repeat_end' and 'repetition_count' can be defined. Please remove one of those values from your request and try again."
        )

    if repeat_start is None:
        repeat_start = datetime.utcnow()

    repeat_start = _datetime_to_iso8601_str(repeat_start)

    if repeat_end is not None:
        repeat_end = _datetime_to_iso8601_str(repeat_end)

    return (repeat_start, repeat_end)
