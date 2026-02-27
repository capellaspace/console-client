import uuid

import random
import pytest

from capella_console_client.config import CONSOLE_API_URL
from capella_console_client import CapellaConsoleClient
from capella_console_client.exceptions import TaskNotCompleteError, ContractNotFoundError
from .test_data import get_mock_responses, post_mock_responses

mock_geojson = {"coordinates": [-105.120360, 39.965330], "type": "Point"}


def test_get_task(test_client, authed_tasking_request_mock, disable_validate_uuid):
    task = test_client.get_task("abc")

    assert task == get_mock_responses("/task/abc")
    assert task["properties"]["taskingrequestId"] == "abc"


def test_task_is_completed(authed_tasking_request_mock, disable_validate_uuid):
    client = CapellaConsoleClient(api_key="MOCK_API_KEY")
    task = client.get_task("abc")

    assert client.is_task_completed(task)


def test_get_collects_for_task(test_client, authed_tasking_request_mock, disable_validate_uuid):
    authed_tasking_request_mock.add_response(
        url=f"{CONSOLE_API_URL}/collects/list/abc",
        json=get_mock_responses("/collects/list/abc"),
    )

    collects = test_client.get_collects_for_task("abc")

    assert collects == get_mock_responses("/collects/list/abc")


def test_get_collects_for_task_not_completed(test_client, auth_httpx_mock, disable_validate_uuid):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/task/def",
        json=get_mock_responses("/task/def"),
    )

    # we should get task 'def', see that it's not completed, and throw an exception
    with pytest.raises(TaskNotCompleteError):
        test_client.get_collects_for_task("def")


def test_create_task_returns_new_task(test_client, authed_tasking_request_mock):
    tasking_requests = test_client.create_tasking_request(geometry=mock_geojson, name="test")
    assert tasking_requests == post_mock_responses("/task")


def test_create_task_invalid_window_open(test_client):
    with pytest.raises(ValueError):
        test_client.create_tasking_request(geometry=mock_geojson, name="test", window_open="PANDA")


def test_create_task_invalid_window_close(test_client):
    with pytest.raises(ValueError):
        test_client.create_tasking_request(geometry=mock_geojson, name="test", window_close="PANDA")


def test_create_task_with_valid_contract_id(test_client, authed_tasking_request_mock):
    tasking_request = test_client.create_tasking_request(geometry=mock_geojson, name="test", contract_id="contract-123")
    assert tasking_request == post_mock_responses("/task")


def test_create_task_with_invalid_contract_id(test_client, auth_httpx_mock):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/task",
        method="POST",
        status_code=400,
        json={"error": {"message": "Contract not found", "code": "CONTRACT_NOT_FOUND"}},
    )
    with pytest.raises(ContractNotFoundError):
        test_client.create_tasking_request(geometry=mock_geojson, name="test", contract_id="invalid-contract")


def test_cancel_success_single_task(verbose_test_client, task_cancel_success_mock):
    tr_id = str(uuid.uuid4())
    result = verbose_test_client.cancel_tasking_requests(tr_id)

    assert len(result.keys()) == 1
    assert result[tr_id]["success"]


def test_cancel_success_multiple_tasks(verbose_test_client, task_cancel_success_mock):
    tr_ids = [str(uuid.uuid4()) for _ in range(random.randint(10, 20))]
    result = verbose_test_client.cancel_tasking_requests(*tr_ids)

    assert len(result.keys()) == len(tr_ids)

    for tr_id in tr_ids:
        assert result[tr_id]["success"]


def test_cancel_success_single_fail(verbose_test_client, task_cancel_error_mock):
    tr_id = str(uuid.uuid4())
    result = verbose_test_client.cancel_tasking_requests(tr_id)

    assert len(result.keys()) == 1
    assert not result[tr_id]["success"]
    assert result[tr_id]["error"]["code"] == "UNABLE_TO_UPDATE_FINALIZED_TRANSACTION"


def test_cancel_success_partial_fail(verbose_test_client, task_cancel_partial_success_mock):
    tr_id_success = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    tr_id_error = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    result = verbose_test_client.cancel_tasking_requests(tr_id_success, tr_id_error)

    assert len(result.keys()) == 2
    assert result[tr_id_success]["success"]
    assert not result[tr_id_error]["success"]
    assert result[tr_id_error]["error"]["code"] == "UNABLE_TO_UPDATE_FINALIZED_TRANSACTION"
