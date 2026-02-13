from unittest.mock import ANY
from capella_console_client.config import CONSOLE_API_URL
from tests.test_data import get_mock_responses


import json


def test_search_all_trs_for_user(test_client, authed_tasking_request_mock):
    tr_results = test_client.search_tasking_requests()

    request = authed_tasking_request_mock.get_request(
        method="POST",
        url=f"{CONSOLE_API_URL}/tasks/search?page=1&limit=250",
    )
    request_payload = json.loads(request.read())
    assert request_payload["query"]["userId"] == "MOCK_ID"

    assert tr_results[:] == get_mock_responses("/tasks/search?page=1&limit=250")["results"]


def test_search_all_trs_for_org(test_client, authed_tasking_request_mock):
    tr_results = test_client.search_tasking_requests(for_org=True)

    request = authed_tasking_request_mock.get_request(
        method="POST",
        url=f"{CONSOLE_API_URL}/tasks/search?page=1&limit=250",
    )
    request_payload = json.loads(request.read())
    assert request_payload["query"]["organizationIds"] == ["MOCK_ORG_ID"]

    assert tr_results[:] == get_mock_responses("/tasks/paged?page=1&limit=100&organizationId=MOCK_ORG_ID")["results"]


def test_search_trs_with_id_single(test_client, authed_tasking_request_mock, disable_validate_uuid):
    authed_tasking_request_mock.reset(assert_all_responses_were_requested=False)
    mock_id = "/tasks/search?page=1&limit=250#SINGLETASK"
    mock_response = get_mock_responses(mock_id)

    single_tr_id = mock_response["results"][0]["properties"]["taskingrequestId"]
    authed_tasking_request_mock.add_response(
        url=f"{CONSOLE_API_URL}{mock_id.split('#')[0]}",
        match_json={
            "query": {"includeRepeatingTasks": {"eq": False}, "taskingrequestIds": {"eq": single_tr_id}, "userId": ANY}
        },
        json=mock_response,
    )

    tr_results = test_client.search_tasking_requests(tasking_request_id="abc")

    assert len(tr_results) == 1
    assert tr_results[0]["properties"]["taskingrequestId"] == single_tr_id


def test_search_trs_with_id_multiple(test_client, authed_tasking_request_mock, disable_validate_uuid):
    tr_results = test_client.search_tasking_requests(tasking_request_id=["abc", "def"])
    assert len(tr_results) == 2

    found_ids = [t["properties"]["taskingrequestId"] for t in tr_results]
    assert "abc" in found_ids
    assert "def" in found_ids


def test_serch_trs_with_id_single_status(test_client, authed_tasking_request_mock, disable_validate_uuid):
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

    tr_results = test_client.search_tasking_requests(status="completed")
    assert len(tr_results) == 1
    assert tr_results[0]["properties"]["taskingrequestId"] == single_tr_id


def test_search_tasking_with_id_multi_status_case_insensitive(
    test_client, authed_tasking_request_mock, disable_validate_uuid
):
    test_client.search_tasking_requests(status=["accepted", "Review", "SUBMITTED"])
    request = authed_tasking_request_mock.get_request(
        method="POST",
        url=f"{CONSOLE_API_URL}/tasks/search?page=1&limit=250",
    )

    request_payload = json.loads(request.read())
    assert set(request_payload["query"]["lastStatusCode"]) == {"accepted", "review", "submitted"}


def test_search_trs_with_id_single_status_with_ids(test_client, authed_tasking_request_mock, disable_validate_uuid):
    test_client.search_tasking_requests(tasking_request_id=["abc", "def"], status=["accepted", "Review", "SUBMITTED"])
    request = authed_tasking_request_mock.get_request(
        method="POST",
        url=f"{CONSOLE_API_URL}/tasks/search?page=1&limit=250",
    )

    request_payload = json.loads(request.read())
    assert set(request_payload["query"]["lastStatusCode"]) == {"accepted", "review", "submitted"}
    assert set(request_payload["query"]["taskingrequestIds"]) == {"abc", "def"}


def test_search_trs_with_id_single_status_nonexistent_omitted(
    test_client, authed_tasking_request_mock, disable_validate_uuid
):
    tr_results = test_client.search_tasking_requests(tasking_request_id=["abc", "def"], status="doesnotexist-status")
    assert len(tr_results) == 2
    assert tr_results[0]["properties"]["taskingrequestId"] == "abc"
    assert tr_results[1]["properties"]["taskingrequestId"] == "def"
