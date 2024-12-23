from datetime import datetime, timezone
import dateutil.parser
from typing import List, Optional, Dict, Any

from capella_console_client.session import CapellaConsoleSession


def get_order(session: CapellaConsoleSession, stac_ids: List[str]) -> Optional[str]:
    """
    find active order containing ALL specified `stac_ids`

    Args:
        stac_ids: STAC IDs that active order should include
    """
    order_id = None
    active_orders = get_non_expired_orders(session=session)
    if not active_orders:
        return None

    for ord in active_orders:
        granules = set([i["granuleId"] for i in ord["items"]])
        if granules.issuperset(stac_ids):
            order_id = ord["orderId"]
            break
    return order_id


def get_non_expired_orders(session: CapellaConsoleSession) -> List[Dict[str, Any]]:
    params = {"customerId": session.customer_id}
    res = session.get("/orders", params=params)

    all_orders = res.json()

    ordered_by_exp_date = sorted(all_orders, key=lambda x: x["expirationDate"])
    now = datetime.now(tz=timezone.utc)

    active_orders = []
    while ordered_by_exp_date:
        cur = ordered_by_exp_date.pop()
        cur_exp_date = dateutil.parser.parse(cur["expirationDate"], ignoretz=False)
        if cur_exp_date < now:
            break
        active_orders.append(cur)

    return active_orders
