import uuid
import pytest
import random

from .test_data import post_mock_responses
from capella_console_client.config import CONSOLE_API_URL
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


def test_create_repeat_request_with_invalid_contract_id(test_client, auth_httpx_mock):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/repeat-requests",
        method="POST",
        status_code=400,
        json={"error": {"message": "Contract not found", "code": "CONTRACT_NOT_FOUND"}},
    )
    with pytest.raises(ContractNotFoundError):
        test_client.create_repeat_request(geometry=mock_geojson, name="test", contract_id="invalid-contract")


def test_cancel_success_single_repeat(test_client, task_cancel_success_mock):
    rr_id = str(uuid.uuid4())
    result = test_client.cancel_repeat_requests(rr_id)

    assert len(result.keys()) == 1
    assert result[rr_id]["success"]


def test_cancel_success_multiple_tasks(test_client, task_cancel_success_mock):
    rr_ids = [str(uuid.uuid4()) for _ in range(random.randint(10, 20))]
    result = test_client.cancel_repeat_requests(*rr_ids)

    assert len(result.keys()) == len(rr_ids)

    for rr_id in rr_ids:
        assert result[rr_id]["success"]


def test_cancel_success_single_fail(test_client, task_cancel_error_mock):
    rr_id = str(uuid.uuid4())
    result = test_client.cancel_repeat_requests(rr_id)

    assert len(result.keys()) == 1
    assert not result[rr_id]["success"]
    assert result[rr_id]["error"]["code"] == "UNABLE_TO_UPDATE_FINALIZED_TRANSACTION"


def test_cancel_success_partial_fail(test_client, task_cancel_partial_success_mock):
    rr_id_success = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    rr_id_error = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    result = test_client.cancel_repeat_requests(rr_id_success, rr_id_error)

    assert len(result.keys()) == 2
    assert result[rr_id_success]["success"]
    assert not result[rr_id_error]["success"]
    assert result[rr_id_error]["error"]["code"] == "UNABLE_TO_UPDATE_FINALIZED_TRANSACTION"
