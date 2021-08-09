import uuid

from typing import no_type_check, Optional, List, Dict, Any

from capella_console_client.enumerations import ProductType, AssetType


@no_type_check
def _validate_uuid(uuid_str: str) -> None:
    try:
        uuid.UUID(uuid_str)
    except ValueError as e:
        raise ValueError(f"{uuid_str} is not a valid uuid: {e}")


def _validate_stac_id_or_stac_items(
    stac_ids: Optional[List[str]] = None, items: Optional[List[Dict[str, Any]]] = None
) -> List[str]:
    if not stac_ids and not items:
        raise ValueError("Please provide stac_ids or items")

    if not stac_ids:
        stac_ids = [f["id"] for f in items]  # type: ignore

    return stac_ids


def _validate_and_filter_product_types(product_types: List[str]) -> List[str]:
    if not product_types:
        return None
    return [p.upper() for p in product_types if p.upper() in ProductType]


def _validate_and_filter_asset_types(asset_types: List[str]) -> List[str]:
    if not asset_types:
        return None
    return [a for a in asset_types if a in AssetType]


def _must_be_int(val):
    try:
        int(val.strip())
    except Exception:
        return "Not an integer"
    return True


def _validate_bbox(val):
    err_msg = "Please specify as bbox list, e.g. [10, 10, 40, 40]"
    try:
        parsed = json.loads(val)
    except:
        return err_msg

    if not isinstance(parsed, list):
        return err_msg

    if not len(parsed) == 4:
        return err_msg
    return True


def get_validator(field_descriptor):
    return {
        int: _must_be_int,
        "bbox": _validate_bbox,
    }.get(field_descriptor)
