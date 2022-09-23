from copy import deepcopy
from pathlib import Path
from typing import Dict, Any

from capella_console_client.cli.cache import CLICache
from capella_console_client.config import ALL_SUPPORTED_FIELDS
from capella_console_client.enumerations import (
    InstrumentMode,
    ProductClass,
    ObservationDirection,
    OrbitState,
    OrbitalPlane,
    ProductType,
    BaseEnum,
)


class SearchFilterOrderOption(str, BaseEnum):
    console_ui = "console UI filters on top"
    alphabetical = "alphabetical"
    # TODO
    # custom = "custom"


DEFAULT_SEARCH_RESULT_HEADERS = [
    "id",
    "instrument_mode",
    "product_type",
    "polarizations",
    "incidence_angle",
]

DEFAULT_SETTINGS = {
    "limit": 50,
    "search_headers": DEFAULT_SEARCH_RESULT_HEADERS,
    "out_path": str(Path.home()),
    "order_list_limit": 50,
    "search_filter_order": SearchFilterOrderOption.console_ui.name,
}


USER_SETTINGS = CLICache.load_user_settings()

CURRENT_SETTINGS: Dict[str, Any] = {**DEFAULT_SETTINGS, **USER_SETTINGS}


CLI_SEARCH_FIELDS = [
    "instrument_mode",
    "product_type",
    "bbox",
    "datetime",
    "orbit_state",
    "observation_direction",
    "incidence_angle",
    "resolution_range",
    "resolution_azimuth",
    "product_category",
    "collections",
    "ids",
    "limit",
    "center_frequency",
    "collect_id",
    "constellation",
    "frequency_band",
    "instruments",
    "look_angle",
    "looks_azimuth",
    "looks_equivalent_number",
    "looks_range",
    "pixel_spacing_azimuth",
    "pixel_spacing_range",
    "platform",
    "polarizations",
    "resolution_ground_range",
    "squint_angle",
    "orbital_plane",
    "billable_area",
]


def get_cli_supported_search_filters():
    if CURRENT_SETTINGS["search_filter_order"] == SearchFilterOrderOption.alphabetical:
        return sorted(CLI_SEARCH_FIELDS)
    return CLI_SEARCH_FIELDS


CLI_SUPPORTED_SEARCH_FILTERS = get_cli_supported_search_filters()

CLI_SUPPORTED_RESULT_HEADERS = deepcopy(CLI_SUPPORTED_SEARCH_FILTERS)
CLI_SUPPORTED_RESULT_HEADERS[CLI_SUPPORTED_RESULT_HEADERS.index("ids")] = "id"
CLI_SUPPORTED_RESULT_HEADERS[CLI_SUPPORTED_RESULT_HEADERS.index("collections")] = "collection"

PROMPT_OPERATORS = {
    "billable_area",
    "center_frequency",
    "datetime",
    "incidence_angle",
    "look_angle",
    "looks_azimuth",
    "looks_equivalent_number",
    "looks_range",
    "pixel_spacing_azimuth",
    "pixel_spacing_range",
    "resolution_azimuth",
    "resolution_ground_range",
    "resolution_range",
    "squint_angle",
}


ENUM_CHOICES_BY_FIELD_NAME = {
    "instrument_mode": InstrumentMode,
    "observation_direction": ObservationDirection,
    "orbital_plane": OrbitalPlane,
    "orbit_state": OrbitState,
    "product_category": ProductClass,
    "product_type": ProductType,
}

COLLECTIONS = [
    "capella-cphd",
    "capella-gec",
    "capella-geo",
    "capella-open-data",
    "capella-sicd",
    "capella-sidd",
    "capella-slc",
    "other",
]
