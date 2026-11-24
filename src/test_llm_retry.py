
import llm
from unittest.mock import patch


class FakeAPIError(Exception):
    def __init__(self, code):
        super().__init__(f"Simulated API error {code}")
        self.code = code


class FakeResponse:
    text = "Simulated successful response"


def test_retry_success():

    responses = [
        FakeAPIError(503),
        FakeAPIError(503),
        FakeResponse()
    ]

    with patch.object(llm, "APIError", FakeAPIError):
        with patch.object(
            llm.client.models,
            "generate_content",
            side_effect=responses
        ) as mock_api:

            with patch.object(llm.time, "sleep"):
                with patch.object(llm.random, "uniform", return_value=0.1):

                    result = llm.call_llm("Test prompt")

    assert result == "Simulated successful response"
    assert mock_api.call_count == 3

    print("PASS: Retried twice after 503 errors.")
    print("PASS: Third attempt succeeded.")
    print("Total API attempts:", mock_api.call_count)


def test_no_retry_for_permanent_error():

    error = FakeAPIError(401)

    with patch.object(llm, "APIError", FakeAPIError):
        with patch.object(
            llm.client.models,
            "generate_content",
            side_effect=error
        ) as mock_api:

            try:
                llm.call_llm("Test prompt")
            except FakeAPIError:
                pass

    assert mock_api.call_count == 1

    print("PASS: Permanent error was not retried.")
    print("Total API attempts:", mock_api.call_count)


def test_fallback_activation():

    responses = [
        FakeAPIError(503),
        FakeAPIError(503),
        FakeAPIError(503),
        FakeResponse()
    ]

    with patch.object(llm, "APIError", FakeAPIError):
        with patch.object(
            llm.client.models,
            "generate_content",
            side_effect=responses
        ) as mock_api:

            with patch.object(llm.time, "sleep"):
                with patch.object(
                    llm.random, "uniform", return_value=0.1
                ):
                    result = llm.call_llm("Test fallback")

    assert result == "Simulated successful response"
    assert mock_api.call_count == 4
    assert llm.LAST_USED_MODEL == llm.FALLBACK_MODEL

    print("PASS: Primary model failed 3 times.")
    print("PASS: Fallback model was activated.")
    print("PASS: Fallback response returned.")
    print("Model recorded:", llm.LAST_USED_MODEL)
    print("Total attempts:", mock_api.call_count)


if __name__ == "__main__":
    test_retry_success()
    test_no_retry_for_permanent_error()
    test_fallback_activation()
