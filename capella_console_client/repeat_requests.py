from typing import Optional, Dict, Any, List, Union
from datetime import datetime, timedelta

import geojson
from dateutil.parser import parse, ParserError

from capella_console_client.session import CapellaConsoleSession
from capella_console_client.validate import _snake_to_camel
from capella_console_client.enumerations import (
    ObservationDirection,
    OrbitState,
    ProductType,
    ProductClass,
    OrbitalPlane,
    RepeatCollectionTier,
    InstrumentMode,
    Polarization,
    ArchiveHoldback,
)

COLLECT_CONSTRAINTS_KEYS = set(
    [
        "collect_mode",
        "look_direction",
        "asc_dsc",
        "orbital_planes",
        "local_time",
        "off_nadir_min",
        "off_nadir_max",
        "elevation_min",
        "elevation_max",
        "image_length",
        "image_width",
        "azimuth",
        "grr_min",
        "grr_max",
        "srr_min",
        "srr_max",
        "azr_min",
        "azr_max",
        "nesz_max",
        "num_looks",
        "polarization",
    ]
)

REPETITION_PROPERTIES_KEYS = set(
    [
        "repeat_start",
        "repeat_end",
        "repetition_interval",
        "repetition_count",
        "maintain_scene_framing",
        "look_angle_tolerance",
    ]
)


def create_repeat_request(
    session: CapellaConsoleSession,
    geometry: geojson.geometry.Geometry,
    name: Optional[str] = "",
    description: Optional[str] = "",
    collection_tier: Optional[Union[str, RepeatCollectionTier]] = RepeatCollectionTier.routine,
    product_category: Optional[Union[str, ProductClass]] = ProductClass.standard,
    archive_holdback: Optional[Union[str, ArchiveHoldback]] = ArchiveHoldback.none,
    custom_attribute_1: Optional[str] = None,
    custom_attribute_2: Optional[str] = None,
    product_types: Optional[List[Union[str, ProductType]]] = None,
    # Repetition properties
    repeat_start: Optional[Union[datetime, str]] = None,
    repeat_end: Optional[Union[datetime, str]] = None,
    repetition_interval: Optional[int] = 7,
    repetition_count: Optional[int] = None,
    maintain_scene_framing: Optional[bool] = False,
    look_angle_tolerance: Optional[int] = None,
    # Collect constraints
    collect_mode: Optional[Union[str, InstrumentMode]] = InstrumentMode.spotlight,
    look_direction: Optional[Union[str, ObservationDirection]] = ObservationDirection.either,
    asc_dsc: Optional[Union[str, OrbitState]] = OrbitState.either,
    orbital_planes: Optional[List[Union[int, OrbitalPlane]]] = None,
    local_time: Optional[List[int]] = None,
    off_nadir_min: Optional[int] = None,
    off_nadir_max: Optional[int] = None,
    elevation_min: Optional[int] = None,
    elevation_max: Optional[int] = None,
    image_length: Optional[int] = None,
    image_width: Optional[int] = None,
    azimuth: Optional[int] = None,
    grr_min: Optional[int] = None,
    grr_max: Optional[int] = None,
    srr_min: Optional[int] = None,
    srr_max: Optional[int] = None,
    azr_min: Optional[int] = None,
    azr_max: Optional[int] = None,
    nesz_max: Optional[int] = None,
    num_looks: Optional[int] = None,
    polarization: Optional[Union[str, Polarization]] = None,
) -> Dict[str, Any]:

    if isinstance(repeat_start, str):
        try:
            repeat_start = parse(repeat_start)
        except ParserError:
            raise ValueError("Could not parse repeat_start string into a useable datetime")
    if isinstance(repeat_end, str):
        try:
            repeat_end = parse(repeat_end)
        except ParserError:
            raise ValueError("Could not parse repeat_end string into a useable datetime")

    if not repeat_start:
        repeat_start = datetime.utcnow()

    repeat_start = repeat_start.isoformat(timespec="milliseconds") + "Z"
    if repeat_end is not None:
        repeat_end = repeat_end.isoformat(timespec="milliseconds") + "Z"

    loc = locals()
    collect_constraints = {_snake_to_camel(k): loc[k] for k in COLLECT_CONSTRAINTS_KEYS if k in loc and loc[k]}
    repetition_properties = {_snake_to_camel(k): loc[k] for k in REPETITION_PROPERTIES_KEYS if k in loc and loc[k]}

    payload = {
        "type": "Feature",
        "geometry": geometry,
        "properties": {
            "repeatrequestName": name,
            "repeatrequestDescription": description,
            "windowOpen": repeat_start,
            "windowClose": repeat_end,
            "collectionTier": collection_tier,
            "productCategory": product_category,
            "archiveHoldback": archive_holdback,
            "customAttribute1": custom_attribute_1,
            "customAttribute2": custom_attribute_2,
            "collectConstraints": collect_constraints,
            "repetitionProperties": repetition_properties,
        },
    }

    print(payload)
    if product_types is not None:
        payload["properties"]["processingConfig"] = {"productTypes": product_types}

    return session.post("/repeat-requests", json=payload).json()
