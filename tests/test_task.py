#!/usr/bin/env python

import pytest

from capella_console_client.config import CONSOLE_API_URL
from capella_console_client import CapellaConsoleClient
from capella_console_client.exceptions import (
    TaskNotCompleteError,
)
from .test_data import (
    get_mock_responses,
)


def test_get_task(test_client, authed_tasking_request_mock):
    task = test_client.get_task("abc")

    assert task == get_mock_responses("/task/abc")
    assert task["properties"]["taskingrequestId"] == "abc"


def test_task_is_completed(authed_tasking_request_mock):
    client = CapellaConsoleClient(email="MOCK_EMAIL", password="MOCK_PW")
    task = client.get_task("abc")

    assert client.is_task_completed(task)


def test_get_collects_for_task(test_client, authed_tasking_request_mock):
    authed_tasking_request_mock.add_response(
        url=f"{CONSOLE_API_URL}/collects/list/abc",
        json=get_mock_responses("/collects/list/abc"),
    )

    task = test_client.get_task("abc")
    collects = test_client.get_collects_for_task(task)

    assert collects == get_mock_responses("/collects/list/abc")


def test_get_collects_for_task_not_completed(test_client, auth_httpx_mock):
    auth_httpx_mock.add_response(
        url=f"{CONSOLE_API_URL}/task/def",
        json=get_mock_responses("/task/def"),
    )

    # we should get task 'def', see that it's not completed, and throw an exception
    task = test_client.get_task("def")

    with pytest.raises(TaskNotCompleteError):
        test_client.get_collects_for_task(task)
