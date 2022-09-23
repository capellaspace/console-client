CONSOLE_API_URL = "https://api.capellaspace.com"
DEFAULT_TIMEOUT = 60
DEFAULT_PAGE_SIZE = 1000
DEFAULT_MAX_FEATURE_COUNT = 500


SUPPORTED_SEARCH_FIELDS = {
    "bbox",
    "intersects",
    "collections",
    "ids",
    "limit",
}


SUPPORTED_QUERY_FIELDS = {
    "center_frequency",
    "collect_id",
    "constellation",
    "datetime",
    "frequency_band",
    "incidence_angle",
    "instruments",
    "instrument_mode",
    "look_angle",
    "looks_azimuth",
    "looks_equivalent_number",
    "looks_range",
    "observation_direction",
    "orbit_state",
    "pixel_spacing_azimuth",
    "pixel_spacing_range",
    "platform",
    "product_category",
    "product_type",
    "polarizations",
    "resolution_azimuth",
    "resolution_ground_range",
    "resolution_range",
    "squint_angle",
    "orbital_plane",
    "billable_area",
}

ALL_SUPPORTED_FIELDS = SUPPORTED_SEARCH_FIELDS | SUPPORTED_QUERY_FIELDS

ALL_SUPPORTED_SORTBY = ALL_SUPPORTED_FIELDS | {"id"}

OPERATOR_SUFFIXES = {
    "eq",
    "in",
    "gt",
    "gte",
    "lt",
    "lte",
}  # , "startsWith", "endsWith"} not supported by current STAC server


STAC_PREFIXED_BY_QUERY_FIELDS = {
    "collect_id": "capella:collect_id",
    "product_category": "capella:product_category",
    "resolution_ground_range": "capella:resolution_ground_range",
    "squint_angle": "capella:squint_angle",
    "constellation": "constellation",
    "instruments": "instruments",
    "platform": "platform",
    "center_frequency": "sar:center_frequency",
    "frequency_band": "sar:frequency_band",
    "instrument_mode": "sar:instrument_mode",
    "looks_azimuth": "sar:looks_azimuth",
    "looks_equivalent_number": "sar:looks_equivalent_number",
    "looks_range": "sar:looks_range",
    "observation_direction": "sar:observation_direction",
    "pixel_spacing_azimuth": "sar:pixel_spacing_azimuth",
    "pixel_spacing_range": "sar:pixel_spacing_range",
    "polarizations": "sar:polarizations",
    "product_type": "sar:product_type",
    "resolution_azimuth": "sar:resolution_azimuth",
    "resolution_range": "sar:resolution_range",
    "orbit_state": "sat:orbit_state",
    "incidence_angle": "view:incidence_angle",
    "look_angle": "view:look_angle",
    "orbital_plane": "capella:orbital_plane",
    "billable_area": "capella:billable_area",
}
