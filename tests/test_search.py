#!/usr/bin/env python

import pytest


from .test_data import (
    get_search_test_cases,
)
from capella_console_client import client
from capella_console_client.validate import _validate_uuid


@pytest.mark.parametrize("search_args,expected", get_search_test_cases())
def test_search(search_args, expected, search_client):
    search_client.search(**search_args)
    assert client._paginated_search.call_args[0][1] == expected


def test_validate_uuid_raises():
    with pytest.raises(ValueError):
        _validate_uuid("123")
