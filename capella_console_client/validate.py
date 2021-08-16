import uuid

from typing import no_type_check, Optional, List, Dict, Any, Union

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


def _validate_and_filter_product_types(
    product_types: Optional[List[str]],
) -> Optional[List[str]]:
    if not product_types:
        return None
    return [p.upper() for p in product_types if p.upper() in ProductType]


def _validate_and_filter_asset_types(
    asset_types: Union[List[str], str, None],
) -> Optional[List[str]]:
    if not asset_types:
        return None
    if isinstance(asset_types, str):
        return [a for a in [asset_types] if a in AssetType]
    return [a for a in asset_types if a in AssetType]
