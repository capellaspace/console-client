import json
import uuid
from unittest.mock import ANY

import random
import pytest

from capella_console_client.config import CONSOLE_API_URL
from capella_console_client import CapellaConsoleClient
from capella_console_client.exceptions import TaskNotCompleteError, ContractNotFoundError
from .test_data import get_mock_responses, post_mock_responses, TASK_2

mock_geojson = {"coordinates": [-105.120360, 39.965330], "type": "Point"}


def test_list_all_tasking_requests(test_client, authed_tasking_request_mock):
    tr_results = test_client.list_tasking_requests()
    assert tr_results[:] == get_mock_responses("/tasks/search?page=1&limit=250")["results"]


def test_list_all_tasking_requests_for_org(test_client, authed_tasking_request_mock):
    tr_results = test_client.list_tasking_requests(for_org=True)
    assert tr_results[:] == get_mock_responses("/tasks/paged?page=1&limit=100&organizationId=MOCK_ORG_ID")["results"]


def test_list_tasking_with_id_single(test_client, authed_tasking_request_mock, disable_validate_uuid):
    authed_tasking_request_mock.reset(assert_all_responses_were_requested=False)
    mock_id = "/tasks/search?page=1&limit=250#SINGLETASK"
    mock_response = get_mock_responses(mock_id)

    single_tr_id = mock_response["results"][0]["properties"]["taskingrequestId"]
    authed_tasking_request_mock.add_response(
        url=f"{CONSOLE_API_URL}{mock_id.split('#')[0]}",
        match_json={
            "query": {"includeRepeatingTasks": {"eq": False}, "taskingrequestIds": [single_tr_id], "userId": ANY}
        },
        json=mock_response,
    )

    tr_results = test_client.list_tasking_requests("abc")

    assert len(tr_results) == 1
    assert tr_results[0]["properties"]["taskingrequestId"] == single_tr_id


def test_list_tasking_with_id_multiple(test_client, authed_tasking_request_mock, disable_validate_uuid):
    tr_results = test_client.list_tasking_requests("abc", "def")
    assert len(tr_results) == 2

    found_ids = [t["properties"]["taskingrequestId"] for t in tr_results]
    assert "abc" in found_ids
    assert "def" in found_ids


def test_list_tasking_with_id_single_status(test_client, authed_tasking_request_mock, disable_validate_uuid):
    authed_tasking_request_mock.reset(assert_all_responses_were_requested=False)
    mock_id = "/tasks/search?page=1&limit=250#SINGLETASK"
    mock_response = get_mock_responses(mock_id)

    single_tr_id = mock_response["results"][0]["properties"]["taskingrequestId"]
    authed_tasking_request_mock.add_response(
        url=f"{CONSOLE_API_URL}{mock_id.split('#')[0]}",
        match_json={
            "query": {"includeRepeatingTasks": {"eq": False}, "lastStatusCode": {"eq": "completed"}, "userId": ANY}
        },
        json=mock_response,
    )

    tr_results = test_client.list_tasking_requests(status="completed")
    assert len(tr_results) == 1
    assert tr_results[0]["properties"]["taskingrequestId"] == single_tr_id


def test_list_tasking_with_id_multi_status_case_insensitive(
    test_client, authed_tasking_request_mock, disable_validate_uuid
):
    test_client.list_tasking_requests(status=["accepted", "Review", "SUBMITTED"])
    request = authed_tasking_request_mock.get_request(
        method="POST",
        url=f"{CONSOLE_API_URL}/tasks/search?page=1&limit=250",
    )

    request_payload = json.loads(request.read())
    assert set(request_payload["query"]["lastStatusCode"]) == {"accepted", "review", "submitted"}


def test_list_tasking_with_id_single_status_with_ids(test_client, authed_tasking_request_mock, disable_validate_uuid):
    test_client.list_tasking_requests("abc", "def", status=["accepted", "Review", "SUBMITTED"])
    request = authed_tasking_request_mock.get_request(
        method="POST",
        url=f"{CONSOLE_API_URL}/tasks/search?page=1&limit=250",
    )

    request_payload = json.loads(request.read())
    assert set(request_payload["query"]["lastStatusCode"]) == {"accepted", "review", "submitted"}
    assert set(request_payload["query"]["taskingrequestIds"]) == {"abc", "def"}


def test_list_tasking_with_id_single_status_nonexistent_omitted(
    test_client, authed_tasking_request_mock, disable_validate_uuid
):
    tr_results = test_client.list_tasking_requests("abc", "def", status="doesnotexist-status")
    assert len(tr_results) == 2
    assert tr_results[0]["properties"]["taskingrequestId"] == "abc"
    assert tr_results[1]["properties"]["taskingrequestId"] == "def"


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


def test_cancel_success_single_task(test_client, task_cancel_success_mock):
    tr_id = str(uuid.uuid4())
    result = test_client.cancel_tasking_requests(tr_id)

    assert len(result.keys()) == 1
    assert result[tr_id]["success"]


def test_cancel_success_multiple_tasks(test_client, task_cancel_success_mock):
    tr_ids = [str(uuid.uuid4()) for _ in range(random.randint(10, 20))]
    result = test_client.cancel_tasking_requests(*tr_ids)

    assert len(result.keys()) == len(tr_ids)

    for tr_id in tr_ids:
        assert result[tr_id]["success"]


def test_cancel_success_single_fail(test_client, task_cancel_error_mock):
    tr_id = str(uuid.uuid4())
    result = test_client.cancel_tasking_requests(tr_id)

    assert len(result.keys()) == 1
    assert not result[tr_id]["success"]
    assert result[tr_id]["error"]["code"] == "UNABLE_TO_UPDATE_FINALIZED_TRANSACTION"


def test_cancel_success_partial_fail(test_client, task_cancel_partial_success_mock):
    tr_id_success = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    tr_id_error = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    result = test_client.cancel_tasking_requests(tr_id_success, tr_id_error)

    assert len(result.keys()) == 2
    assert result[tr_id_success]["success"]
    assert not result[tr_id_error]["success"]
    assert result[tr_id_error]["error"]["code"] == "UNABLE_TO_UPDATE_FINALIZED_TRANSACTION"
