#!/usr/bin/env python

import datetime

import pytest

from capella_console_client import CapellaConsoleClient
from .test_data import post_mock_responses
from capella_console_client.exceptions import RepeatRequestPayloadValidationError, ContractNotFoundError

mock_geojson = {"coordinates": [-105.120360, 39.965330], "type": "Point"}


def test_create_repeat_request_returns_new_request(test_client, authed_repeat_request_mock):
    repeat_request = test_client.create_repeat_request(geometry=mock_geojson, name="test")
    assert repeat_request == post_mock_responses("/repeat-requests")


def test_create_repeat_request_invalid_repeat_start(test_client):
    with pytest.raises(ValueError):
        test_client.create_repeat_request(geometry=mock_geojson, name="test", repeat_start="PANDA")


def test_create_repeat_request_invalid_repeat_end(test_client):
    with pytest.raises(ValueError):
        test_client.create_repeat_request(geometry=mock_geojson, name="test", repeat_end="PANDA")


def test_create_repeat_request_end_and_count_defined(test_client):
    with pytest.raises(RepeatRequestPayloadValidationError):
        test_client.create_repeat_request(
            geometry=mock_geojson, name="test", repeat_end="PANDA", repetition_count=12345
        )


def test_create_repeat_request_with_valid_contract_id(test_client, authed_repeat_request_mock):
    repeat_request = test_client.create_repeat_request(geometry=mock_geojson, name="test", contract_id="contract-123")
    assert repeat_request == post_mock_responses("/repeat-requests")


def test_create_repeat_request_with_invalid_contract_id(test_client, authed_repeat_request_mock):
    with pytest.raises(ContractNotFoundError):
        test_client.create_repeat_request(geometry=mock_geojson, name="test", contract_id="invalid-contract")
