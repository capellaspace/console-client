from unittest.mock import ANY
from capella_console_client.config import CONSOLE_API_URL
from tests.test_data import get_mock_responses


import json


def test_search_all_rrs_for_user(test_client, authed_tasking_request_mock):
    rr_results = test_client.search_repeat_requests()

    request = authed_tasking_request_mock.get_request(
        method="POST",
        url=f"{CONSOLE_API_URL}/repeat-requests/search?page=1&limit=250",
    )
    request_payload = json.loads(request.read())
    assert request_payload["filter"]["userId"] == "MOCK_ID"

    assert rr_results[:] == get_mock_responses("/repeat-requests/search?page=1&limit=250")["results"]


def test_search_all_rrs_for_org(test_client, authed_tasking_request_mock):
    rr_results = test_client.search_repeat_requests(for_org=True)

    request = authed_tasking_request_mock.get_request(
        method="POST",
        url=f"{CONSOLE_API_URL}/repeat-requests/search?page=1&limit=250",
    )
    request_payload = json.loads(request.read())
    assert request_payload["filter"]["organizationIds"] == ["MOCK_ORG_ID"]

    assert (
        rr_results[:]
        == get_mock_responses("/repeat-requests/paged?page=1&limit=250&organizationId=MOCK_ORG_ID")["results"]
    )


def test_search_rrs_with_id_single(test_client, authed_tasking_request_mock, disable_validate_uuid):
    authed_tasking_request_mock.reset(assert_all_responses_were_requested=False)
    mock_id = "/repeat-requests/search?page=1&limit=250#SINGLEREPEAT"
    mock_response = get_mock_responses(mock_id)

    single_rr_id = mock_response["results"][0]["properties"]["repeatrequestId"]
    authed_tasking_request_mock.add_response(
        url=f"{CONSOLE_API_URL}{mock_id.split('#')[0]}",
        match_json={"filter": {"repeatrequestIds": {"eq": single_rr_id}, "userId": ANY}},
        json=mock_response,
    )

    rr_results = test_client.search_repeat_requests(repeat_request_id=single_rr_id)

    assert len(rr_results) == 1
    assert rr_results[0]["properties"]["repeatrequestId"] == single_rr_id


def test_search_rrs_with_id_multiple(test_client, authed_tasking_request_mock, disable_validate_uuid):
    rr_results = test_client.search_repeat_requests(repeat_request_id=["PANDA", "BOAR"])
    assert len(rr_results) == 2

    found_ids = [t["properties"]["repeatrequestId"] for t in rr_results]
    assert "PANDA" in found_ids
    assert "BOAR" in found_ids


def test_search_rrs_with_id_single_status(test_client, authed_tasking_request_mock, disable_validate_uuid):
    authed_tasking_request_mock.reset(assert_all_responses_were_requested=False)
    mock_id = "/repeat-requests/search?page=1&limit=250#SINGLEREPEAT"
    mock_response = get_mock_responses(mock_id)

    single_rr_id = mock_response["results"][0]["properties"]["repeatrequestId"]
    authed_tasking_request_mock.add_response(
        url=f"{CONSOLE_API_URL}{mock_id.split('#')[0]}",
        match_json={"filter": {"lastStatusCode": {"eq": "received"}, "userId": ANY}},
        json=mock_response,
    )

    rr_results = test_client.search_repeat_requests(status="received")
    assert len(rr_results) == 1
    assert rr_results[0]["properties"]["repeatrequestId"] == single_rr_id


def test_search_rrs_with_id_multi_status_case_insensitive(
    test_client, authed_tasking_request_mock, disable_validate_uuid
):
    test_client.search_repeat_requests(status=["accepted", "Review", "SUBMITTED"])
    request = authed_tasking_request_mock.get_request(
        method="POST",
        url=f"{CONSOLE_API_URL}/repeat-requests/search?page=1&limit=250",
    )

    request_payload = json.loads(request.read())
    assert set(request_payload["filter"]["lastStatusCode"]) == {"accepted", "review", "submitted"}


def test_search_rrs_with_id_single_status_with_ids(test_client, authed_tasking_request_mock, disable_validate_uuid):
    test_client.search_repeat_requests(repeat_request_id=["abc", "def"], status=["accepted", "Review", "SUBMITTED"])
    request = authed_tasking_request_mock.get_request(
        method="POST",
        url=f"{CONSOLE_API_URL}/repeat-requests/search?page=1&limit=250",
    )

    request_payload = json.loads(request.read())
    assert set(request_payload["filter"]["lastStatusCode"]) == {"accepted", "review", "submitted"}
    assert set(request_payload["filter"]["repeatrequestIds"]) == {"abc", "def"}


def test_search_rrs_with_id_single_status_nonexistent_omitted(
    test_client, authed_tasking_request_mock, disable_validate_uuid
):
    rr_results = test_client.search_repeat_requests(repeat_request_id=["PANDA", "BOAR"], status="doesnotexist-status")
    assert len(rr_results) == 2
    assert rr_results[0]["properties"]["repeatrequestId"] == "PANDA"
    assert rr_results[1]["properties"]["repeatrequestId"] == "BOAR"
