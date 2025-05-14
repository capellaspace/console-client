CONSOLE_API_URL = "https://api.capellaspace.com"
CAPELLA_API_KEY_ENV = "CAPELLA_API_KEY"
DEFAULT_TIMEOUT = 60
CATALOG_MAX_PAGE_SIZE = 900
CATALOG_DEFAULT_LIMIT = 500
TASKING_REQUEST_DEFAULT_PAGE_SIZE = 100
STAC_MAX_ITEM_RETURN = 10000


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
    "product_type",
    "polarizations",
    "resolution_azimuth",
    "resolution_ground_range",
    "resolution_range",
    "squint_angle",
    "layover_angle",
    "orbital_plane",
    "billable_area",
    "hash",
    "local_timezone",
    "local_datetime",
    "local_time",
    "epsg",
    "image_formation_algorithm",
    "azimuth_angle",
    "collection_type",
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
    "resolution_ground_range": "capella:resolution_ground_range",
    "squint_angle": "capella:squint_angle",
    "layover_angle": "capella:layover_angle",
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
    "hash": "capella:hash",
    "local_timezone": "locale:timezone",
    "local_datetime": "locale:datetime",
    "local_time": "locale:time",
    "epsg": "proj:epsg",
    "image_formation_algorithm": "capella:image_formation_algorithm",
    "azimuth_angle": "view:azimuth",
    "collection_type": "capella:collection_type",
}

ROOT_LEVEL_GROUPBY_FIELDS = {"id", "collection"}

ALL_SUPPORTED_GROUPBY_FIELDS = ROOT_LEVEL_GROUPBY_FIELDS | SUPPORTED_QUERY_FIELDS
UNKNOWN_GROUPBY_FIELD = "unknown"


_COMMON_COLLECT_CONSTRAINTS_FIELDS = frozenset(
    [
        "off_nadir_min",
        "off_nadir_max",
        "image_width",
        "orbital_planes",
        "asc_dsc",
        "look_direction",
        "local_time",
        "polarization",
        "azimuth_angle_min",
        "azimuth_angle_max",
        "squint",
        "max_squint_angle",
    ]
)
TASKING_REQUEST_COLLECT_CONSTRAINTS_FIELDS = _COMMON_COLLECT_CONSTRAINTS_FIELDS.copy()
REPEAT_REQUEST_COLLECT_CONSTRAINTS_FIELDS = _COMMON_COLLECT_CONSTRAINTS_FIELDS.copy()


REPEAT_REQUESTS_REPETITION_PROPERTIES_FIELDS = frozenset(
    [
        "repeat_start",
        "repeat_end",
        "repetition_interval",
        "repetition_count",
    ]
)
