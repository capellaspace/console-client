#!/usr/bin/env python

import pytest
import httpx
from pytest_httpx import HTTPXMock
from unittest.mock import MagicMock

from .test_data import get_search_test_cases, search_catalog_get_stac_ids
from capella_console_client import client
from capella_console_client import search
from capella_console_client.validate import _validate_uuid
from capella_console_client.search import _paginated_search, _page_search


@pytest.mark.parametrize("search_args,expected", get_search_test_cases())
def test_search(search_args, expected, search_client):
    search_client.search(**search_args)
    assert client._paginated_search.call_args[0][1] == expected


def test_validate_uuid_raises():
    with pytest.raises(ValueError):
        _validate_uuid("123")


def test_paginated_search_single_page(single_page_search_client):
    results = _paginated_search(single_page_search_client._sesh, payload={"limit": 1})
    assert len(results) == 1
    assert results[0] == search_catalog_get_stac_ids()["features"][0]


def test_paginated_search_multi_page(multi_page_search_client):
    results = _paginated_search(multi_page_search_client._sesh, payload={"limit": 10})
    assert len(results) == 10


@pytest.fixture
def outdated_gateway_endpoint(monkeypatch):
    monkeypatch.setattr(
        search,
        "API_GATEWAY",
        "https://phishphish.execute-api.us-west-2.amazonaws.com/prod",
    )


def test_single_page_search_fallback(
    single_page_search_client, outdated_gateway_endpoint, auth_httpx_mock
):
    def raise_connect_error(request, extensions: dict):
        raise httpx.ConnectError("host unknown", request=request)

    auth_httpx_mock.add_callback(
        raise_connect_error, url=f"{search.API_GATEWAY}/search"
    )

    with single_page_search_client._sesh:
        _page_search(single_page_search_client._sesh, payload={"limit": 1})
