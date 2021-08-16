from copy import deepcopy
from pathlib import Path
from typing import Dict, Any

from capella_console_client.cli.cache import CLICache
from capella_console_client.config import ALL_SUPPORTED_FIELDS

CLI_SUPPORTED_SEARCH_FILTERS = sorted(ALL_SUPPORTED_FIELDS)
# no intersects support currently
del CLI_SUPPORTED_SEARCH_FILTERS[CLI_SUPPORTED_SEARCH_FILTERS.index("intersects")]

CLI_SUPPORTED_RESULT_HEADERS = deepcopy(CLI_SUPPORTED_SEARCH_FILTERS)
CLI_SUPPORTED_RESULT_HEADERS[CLI_SUPPORTED_RESULT_HEADERS.index("ids")] = "id"
CLI_SUPPORTED_RESULT_HEADERS[
    CLI_SUPPORTED_RESULT_HEADERS.index("collections")
] = "collection"

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
}


USER_SETTINGS = CLICache.load_user_settings()

CURRENT_SETTINGS: Dict[str, Any] = {**DEFAULT_SETTINGS, **USER_SETTINGS}

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
