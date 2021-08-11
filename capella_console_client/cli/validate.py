"""
CLI / interactive (questionary) specific validation
"""

import json
from pathlib import Path
import re

from capella_console_client.validate import _validate_uuid as _validate_core_uuid


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
    err_msg = "please specify as bbox list, e.g. [10, 10, 40, 40]"
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


def _validate_dir_exists(path_str: str) -> bool:
    err_msg = "please specify a valid uuid (e.g. aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee)"
    p = Path(path_str).resolve()
    return p.exists() and p.is_dir()


def _validate_out_path(path_str: str) -> bool:
    p = Path(path_str).resolve()
    return p.is_absolute() and p.parent.exists() and not p.is_dir()


def _validate_email(email: str):
    err_msg = "please specify a valid email"
    if EMAIL_REGEX.fullmatch(email):
        return True
    return err_msg


def get_validator(field: str):
    custom_validator = {
        "bbox": _validate_bbox,
        "collect_id": _validate_uuid,
    }.get(field)

    if custom_validator:
        return custom_validator

    type_caster = get_caster(field)

    if type_caster:
        return _must_be_type(type_caster)

    return None


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
    }.get(field)
