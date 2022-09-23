"""
CLI / interactive (questionary) specific validation
"""

import json
from pathlib import Path
import re
from dateutil.parser import parse, ParserError
from typing import Union

import typer

from capella_console_client.validate import _validate_uuid as _validate_core_uuid
from capella_console_client.assets import STAC_ID_REGEX


EMAIL_REGEX = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")


def _must_be_type(type):
    def _must_be_type_impl(val):
        try:
            type(val.strip())
        except Exception:
            return f"please provide a valid {type}"
        return True

    return _must_be_type_impl


def _validate_bbox(val):
    err_msg = "please specify as bbox list [<lon upper left>, <lat upper left>, <lon lower right>, <lat lower right>], e.g. [-122.4, 46.9, -124.9, 48.5]"
    if not val:
        return err_msg
    try:
        parsed = json.loads(val)
    except:
        return err_msg

    if not isinstance(parsed, list):
        return err_msg

    if not len(parsed) == 4:
        return err_msg
    return True


def _validate_uuid(val):
    err_msg = "please specify a valid uuid (e.g. aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee)"
    try:
        _validate_core_uuid(val)
    except ValueError as e:
        return err_msg

    return True


def _validate_dir_exists(path_str: str) -> Union[bool, str]:
    err_msg = "please specify an existing directory path"
    p = Path(path_str).resolve()
    if p.exists() and p.is_dir():
        return True
    return err_msg


def _validate_out_path(path_str: str) -> bool:
    p = Path(path_str).resolve()
    return p.is_absolute() and p.parent.exists() and not p.is_dir()


def _validate_email(email: str):
    err_msg = "please specify a valid email"
    if EMAIL_REGEX.fullmatch(email):
        return True
    return err_msg


def _validate_datetime(dt_str: str):
    err_msg = "please specify a valid UTC date(time) (e.g. 2020-08-14 or 2020-08-14 12:00:00)"
    if not dt_str or len(dt_str) < 10:
        return err_msg

    try:
        parse(dt_str)
    except ParserError:
        return err_msg
    return True


def _parse_str_collection(list_str):
    _cur = list_str.strip()
    if not _cur.startswith("[") or not _cur.endswith("]"):
        # raw parse
        separator = "," if "," in _cur else " "
        stac_ids = _cur.split(separator)
    else:
        stac_ids = json.loads(_cur.replace("'", '"'))
    return stac_ids


def _validate_stac_ids(stac_id_str: str):
    err_msg = "please specify one or more , or whitespace separated STAC Ids (e.g. CAPELLA_C03_SM_GEO_HH_20210512034455_20210512034459,CAPELLA_C03_SP_GEO_HH_20210511101416_20210511101439)"

    stac_ids = _parse_str_collection(stac_id_str)
    if all(STAC_ID_REGEX.match(stac_id) for stac_id in stac_ids):
        return True

    return err_msg


def _validate_collections(stac_id_str: str):
    err_msg = "please specify one or more , or whitespace separated collections (e.g. capella-open-data)"

    stac_ids = _parse_str_collection(stac_id_str)
    if all(STAC_ID_REGEX.match(stac_id) for stac_id in stac_ids):
        return True

    return err_msg


def get_validator(field: str):
    custom_validator = {
        "bbox": _validate_bbox,
        "collect_id": _validate_uuid,
        "datetime": _validate_datetime,
        "ids": _validate_stac_ids,
    }.get(field)

    if custom_validator:
        return custom_validator

    type_caster = get_caster(field)

    if type_caster:
        return _must_be_type(type_caster)

    return None


def _cast_dt(val):
    return parse(val).strftime("%Y-%m-%dT%H:%M:%SZ")


def get_caster(field: str):
    return {
        "bbox": json.loads,
        "billable_area": int,
        "center_frequency": float,
        "incidence_angle": float,
        "limit": int,
        "look_angle": float,
        "looks_azimuth": int,
        "looks_equivalent_number": int,
        "looks_range": int,
        "pixel_spacing_azimuth": float,
        "pixel_spacing_range": float,
        "polarizations": float,
        "resolution_azimuth": float,
        "resolution_ground_range": float,
        "resolution_range": float,
        "squint_angle": float,
        "datetime": _cast_dt,
        "ids": _parse_str_collection,
        "collections": _parse_str_collection,
    }.get(field)


def _no_selection_bye(selection, info_msg=None):
    if not info_msg:
        info_msg = "nothing selected ... bye"

    if selection in (None, []):
        typer.echo(info_msg)
        raise typer.Exit(code=1)


def _at_least_one_selected(val):
    err_msg = "Please select at least one option"
    if len(val) < 1:
        return err_msg
    return True
