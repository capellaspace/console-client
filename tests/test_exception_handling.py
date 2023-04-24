from capella_console_client.exceptions import (
    handle_error_response_and_raise,
    CollectionAccessDeniedError,
    OrderExpiredError,
    CapellaConsoleClientError,
)

import pytest
from unittest.mock import MagicMock


def create_mock_response(resp):
    mock = MagicMock()
    mock.json.return_value = resp
    return mock


@pytest.mark.parametrize(
    "error_response,expected_error_class",
    [
        (
            {"error": {"message": "Unknown error", "data": {"cause": "NONONO"}}},
            CapellaConsoleClientError,
        ),
        (
            {
                "error": "Your organization is not permitted to access any of the collections your query is attempting to filter amongst (capella-mock)"
            },
            CollectionAccessDeniedError,
        ),
        ({"error": "order expired"}, OrderExpiredError),
    ],
)
def test_handle_error_response_and_raise(error_response, expected_error_class):
    resp = create_mock_response(error_response)
    with pytest.raises(expected_error_class) as excinfo:
        handle_error_response_and_raise(resp)

    if isinstance(error_response["error"], str):
        assert excinfo.value.message == error_response["error"]
    else:
        assert excinfo.value.message == error_response["error"]["message"]
        assert excinfo.value.data == error_response["error"]["data"]
