#!/usr/bin/env python

import pytest

from .test_data import (
    get_search_test_cases,
    get_canned_search_results,
    get_canned_search_results_multi_page,
)
from capella_console_client.validate import _validate_uuid
from capella_console_client.search import StacSearch


@pytest.mark.parametrize("search_args,expected", get_search_test_cases())
def test_search_payload(search_args, expected, search_client):
    search = StacSearch(search_client._sesh, **search_args)
    assert search.payload == expected


def test_validate_uuid_raises():
    with pytest.raises(ValueError):
        _validate_uuid("123")


def test_paginated_search_single_page(single_page_search_client):
    search = StacSearch(single_page_search_client._sesh, limit=1)
    results = search.fetch_all()
    assert len(results) == 1
    assert results[0] == get_canned_search_results()["features"][0]


def test_paginated_search_limits(multi_page_search_client):
    search = StacSearch(multi_page_search_client._sesh, limit=6)
    results = search.fetch_all()
    assert len(results) == get_canned_search_results_multi_page()["numberMatched"]


def test_search_result_to_feature_collection(multi_page_search_client):
    search = StacSearch(multi_page_search_client._sesh)
    results = search.fetch_all()
    feature_collection = results.to_feature_collection()
    assert feature_collection["type"] == "FeatureCollection"

    page_ret = get_canned_search_results_multi_page()["features"]
    assert feature_collection["features"] == page_ret


def test_search_result_repr(multi_page_search_client):
    search = StacSearch(multi_page_search_client._sesh)
    results = search.fetch_all()
    assert repr(results)
