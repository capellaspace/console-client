from capella_console_client.cli.cache import CLICachePaths
from capella_console_client.config import ALL_SUPPORTED_FIELDS

CLI_SUPPORTED_SEARCH_FILTERS = sorted(ALL_SUPPORTED_FIELDS)

DEFAULT_SEARCH_RESULT_FIELDS = [
    "id",
    "datetime",
    "instrument_mode",
    "product_type",
    "polarizations",
    "incidence_angle",
]

DEFAULT_SETTINGS = {"limit": 50, "search_fields": DEFAULT_SEARCH_RESULT_FIELDS}


USER_SETTINGS = CLICachePaths.safe_load_user_settings()

CURRENT_SETTINGS = {**DEFAULT_SETTINGS, **USER_SETTINGS}


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
