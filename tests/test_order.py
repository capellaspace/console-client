import json

import pytest

from capella_console_client.config import CONSOLE_API_URL
from capella_console_client import client as capella_client_module
from capella_console_client.exceptions import (
    NoValidStacIdsError,
    OrderRejectedError,
    InsufficientFundsError,
)
from .test_data import (
    post_mock_responses,
    get_mock_responses,
)


def test_list_specific_order(test_client, auth_httpx_mock):
    order_id = "179d4c75-8830-4947-ba33-67d8994eabe5"
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders/{order_id}",
        json=get_mock_responses("/orders")[0],
    )
    order = test_client.list_orders(order_id)
    assert order == get_mock_responses("/orders")


def test_list_all_orders(order_client):
    orders = order_client.list_orders()
    assert orders == get_mock_responses("/orders")


def test_list_no_active_orders(order_client):
    orders = order_client.list_orders(is_active=True)
    assert orders == []


def test_list_active_orders_with_order_ids(test_client, monkeypatch, disable_validate_uuid):
    monkeypatch.setattr(
        capella_client_module,
        "get_non_expired_orders",
        lambda session: get_mock_responses("/orders"),
    )

    orders = test_client.list_orders("1", is_active=True)
    assert orders == get_mock_responses("/orders")


def test_list_active_orders(non_expired_order_mock):
    client, non_expired_order = non_expired_order_mock
    active_orders = client.list_orders(is_active=True)
    assert active_orders == [non_expired_order]


def test_review_order(order_client, httpx_mock):
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/catalog/search",
        json={
            "features": [{"id": "MOCK_STAC_ID", "collection": "capella-test"}],
            "numberMatched": 1,
        },
    )
    order_client.review_order(stac_ids=["MOCK_STAC_ID"])


def test_review_order_insufficient_funds(review_client_insufficient_funds, httpx_mock):
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/catalog/search",
        json={
            "features": [{"id": "MOCK_STAC_ID", "collection": "capella-test"}],
            "numberMatched": 1,
        },
    )

    with pytest.raises(InsufficientFundsError):
        review_client_insufficient_funds.review_order(stac_ids=["MOCK_STAC_ID"])


def test_review_order_no_match(order_client, httpx_mock):
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/catalog/search",
        json={"features": [], "numberMatched": 0},
    )
    with pytest.raises(NoValidStacIdsError):
        order_client.review_order(stac_ids=["MOCK_STAC_ID"])


def test_submit_order_not_previously_ordered_check_active_orders(order_client, httpx_mock):
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/catalog/search",
        json={
            "features": [{"id": "MOCK_STAC_ID", "collection": "capella-test"}],
            "numberMatched": 1,
        },
    )

    order_id = order_client.submit_order(stac_ids=["MOCK_STAC_ID"], check_active_orders=True)

    assert order_id == post_mock_responses("/submitOrder")["orderId"]
    order_request = httpx_mock.get_request(method="POST", url=f"{CONSOLE_API_URL}/orders")
    assert json.loads(order_request.read()) == {
        "items": [{"collectionId": "capella-test", "granuleId": "MOCK_STAC_ID"}]
    }


def test_submit_order_not_previously_ordered_no_check_active_orders(
    order_client, httpx_mock, assert_all_responses_were_requested
):
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/catalog/search",
        json={
            "features": [{"id": "MOCK_STAC_ID", "collection": "capella-test"}],
            "numberMatched": 1,
        },
    )
    order_id = order_client.submit_order(stac_ids=["MOCK_STAC_ID"], check_active_orders=False)

    assert order_id == post_mock_responses("/submitOrder")["orderId"]
    order_request = httpx_mock.get_request(method="POST", url=f"{CONSOLE_API_URL}/orders")
    assert json.loads(order_request.read()) == {
        "items": [{"collectionId": "capella-test", "granuleId": "MOCK_STAC_ID"}]
    }


def test_submit_order_previously_ordered(non_expired_order_mock, httpx_mock):
    client, non_expired_order = non_expired_order_mock

    order_id = client.submit_order(
        stac_ids=["CAPELLA_C02_SM_SLC_HH_20201126192221_20201126192225"],
        check_active_orders=True,
    )

    assert order_id == post_mock_responses("/submitOrder")["orderId"]
    assert httpx_mock.get_request(method="POST", url=f"{CONSOLE_API_URL}/orders") is None


def test_submit_order_invalid_stac_id(test_client, httpx_mock):
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/catalog/search",
        method="POST",
        json={"features": [], "numberMatched": 0},
    )

    with pytest.raises(NoValidStacIdsError):
        test_client.submit_order(stac_ids=["DOES_NOT_EXISTS"])


def test_submit_order_rejected(order_client_unsuccessful, httpx_mock):
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/catalog/search",
        method="POST",
        json={
            "features": [
                {
                    "id": "CAPELLA_C02_SM_SLC_HH_20201126192221_20201126192225",
                    "collection": "capella-test",
                }
            ],
            "numberMatched": 1,
        },
    )

    with pytest.raises(OrderRejectedError):
        order_client_unsuccessful.submit_order(stac_ids=["DOES_NOT_EXISTS"])


def test_submit_order_items(order_client, httpx_mock):
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/catalog/search",
        json={
            "features": [{"id": "MOCK_STAC_ID", "collection": "capella-test"}],
            "numberMatched": 1,
        },
    )

    order_id = order_client.submit_order(
        items=[{"id": "MOCK_STAC_ID", "collection": "capella-test"}],
        check_active_orders=False,
    )

    assert order_id == post_mock_responses("/submitOrder")["orderId"]
    order_request = httpx_mock.get_request(method="POST", url=f"{CONSOLE_API_URL}/orders")
    assert json.loads(order_request.read()) == {
        "items": [{"collectionId": "capella-test", "granuleId": "MOCK_STAC_ID"}]
    }


def test_submit_order_items_omit_search(order_client, httpx_mock):
    order_id = order_client.submit_order(
        items=[{"id": "MOCK_STAC_ID", "collection": "capella-test"}],
        check_active_orders=False,
        omit_search=True,
    )

    assert order_id == post_mock_responses("/submitOrder")["orderId"]
    order_request = httpx_mock.get_request(method="POST", url=f"{CONSOLE_API_URL}/orders")
    assert json.loads(order_request.read()) == {
        "items": [{"collectionId": "capella-test", "granuleId": "MOCK_STAC_ID"}]
    }


def test_submit_order_missing_input(test_client):
    with pytest.raises(ValueError):
        test_client.submit_order()


def test_get_stac_items_of_order_ids_only(non_expired_order_mock, httpx_mock, disable_validate_uuid):
    client, _ = non_expired_order_mock

    stac_ids = ["CAPELLA_C02_SM_SLC_HH_20201126192221_20201126192225"]
    order_id = client.submit_order(
        stac_ids=stac_ids,
        check_active_orders=True,
    )
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders/{order_id}",
        json=get_mock_responses("/orders")[0],
    )

    retrieved_stac_ids = client.get_stac_items_of_order(order_id, ids_only=True)
    assert retrieved_stac_ids == stac_ids


def test_get_stac_items_of_order(non_expired_order_mock, httpx_mock, disable_validate_uuid):
    client, _ = non_expired_order_mock

    stac_ids = ["CAPELLA_C02_SM_SLC_HH_20201126192221_20201126192225"]
    order_id = client.submit_order(
        stac_ids=stac_ids,
        check_active_orders=True,
    )
    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/orders/{order_id}",
        json=get_mock_responses("/orders")[0],
    )

    httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/catalog/search",
        json={
            "features": [{"id": "CAPELLA_C02_SM_SLC_HH_20201126192221_20201126192225"}],
            "numberMatched": 1,
        },
    )
    ret = client.get_stac_items_of_order(order_id)
    assert [r["id"] for r in ret] == stac_ids
