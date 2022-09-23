from typing import Dict, List, Any, Optional

from capella_console_client.logconf import logger


def _sort_stac_items(items: List[Dict[str, Any]], stac_ids: List[str]) -> List[Dict[str, Any]]:
    """
    sort items by stac_ids

    Args:
        items (List[Dict[str, Any]]): stac items
        stac_ids (List[str]): stac ids to sort by

    Returns:
        List[Dict[str, Any]]: stac items sorted by stac_ids
    """
    if len(stac_ids) != len(items):
        logger.warning(f"wrong size stac_ids ({len(stac_ids)} instead of {len(items)})... omitting sort ")
        return items

    sorted = []
    item_ids = [s["id"] for s in items]
    for stac_id in stac_ids:
        try:
            cur = items[item_ids.index(stac_id)]
        except ValueError:
            continue
        sorted.append(cur)

    not_in_items = [item for item in items if item["id"] not in stac_ids]
    sorted.extend(not_in_items)
    return sorted
