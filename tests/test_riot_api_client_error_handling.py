from urllib.parse import quote
from unittest.mock import MagicMock, patch
import pytest
import httpx

from app.riot.riotApiClient import RiotApiClient


class DummyResponseWithStatus:

    def __init__(self, status_code, payload=None, headers=None):
        self.status_code = status_code
        self.payload = payload or {}
        self.headers = headers or {}
        self._text = "Error response"

    def raise_for_status(self):
        if 400 <= self.status_code < 600:
            raise httpx.HTTPStatusError(
                "Error",
                request=MagicMock(),
                response=self,
            )

    def json(self):
        return self.payload

    @property
    def text(self):
        return self._text


class ClientWithException:

    def __init__(self, response):
        self.response = response
        self.call_count = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, headers=None, params=None):
        self.call_count += 1
        return self.response


class ClientWithRetryableError:

    def __init__(self, error_response, success_response, num_errors=1):
        self.error_response = error_response
        self.success_response = success_response
        self.call_count = 0
        self.num_errors = num_errors

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def get(self, url, headers=None, params=None):
        self.call_count += 1
        if self.call_count <= self.num_errors:
            return self.error_response
        return self.success_response


class TestRiotApiClientErrorHandling:

    def test_http_429_rate_limited_retries_with_retry_after_header(self, monkeypatch):
        """Test that 429 errors with Retry-After header are handled with backoff."""
        import time

        response_429 = DummyResponseWithStatus(429, headers={"Retry-After": "1"})
        response_ok = DummyResponseWithStatus(200, payload={"data": "success"})

        client = ClientWithRetryableError(response_429, response_ok, num_errors=1)

        def fake_client_factory(*, timeout):
            return client

        monkeypatch.setattr("app.riot.riotApiClient.httpx.Client", fake_client_factory)
        monkeypatch.setattr("app.riot.riotApiClient.time.sleep", lambda x: None)  # Skip actual sleep

        api_client = RiotApiClient(api_key="test-key", regional_routing="europe")
        result = api_client.get_match_info_by_match_id("EUW1_123")

        assert result == {"data": "success"}
        assert client.call_count == 2  # First call fails, retry succeeds

    def test_http_429_rate_limited_retries_without_retry_after_header(self, monkeypatch):
        """Test that 429 errors without Retry-After use exponential backoff."""
        response_429 = DummyResponseWithStatus(429, headers={})
        response_ok = DummyResponseWithStatus(200, payload={"data": "success"})

        client = ClientWithRetryableError(response_429, response_ok, num_errors=1)

        def fake_client_factory(*, timeout):
            return client

        monkeypatch.setattr("app.riot.riotApiClient.httpx.Client", fake_client_factory)
        monkeypatch.setattr("app.riot.riotApiClient.time.sleep", lambda x: None)

        api_client = RiotApiClient(api_key="test-key", regional_routing="europe", max_retries=2)
        result = api_client.get_match_info_by_match_id("EUW1_123")

        assert result == {"data": "success"}
        assert client.call_count == 2

    def test_http_429_exceeds_max_retries_raises_error(self, monkeypatch):
        """Test that 429 errors that exceed max_retries raise the error."""
        response_429 = DummyResponseWithStatus(429, headers={})

        client = ClientWithException(response_429)

        def fake_client_factory(*, timeout):
            return client

        monkeypatch.setattr("app.riot.riotApiClient.httpx.Client", fake_client_factory)
        monkeypatch.setattr("app.riot.riotApiClient.time.sleep", lambda x: None)

        api_client = RiotApiClient(api_key="test-key", regional_routing="europe", max_retries=1)

        with pytest.raises(httpx.HTTPStatusError):
            api_client.get_match_info_by_match_id("EUW1_123")

    def test_http_500_server_error_retries(self, monkeypatch):
        """Test that 500-599 errors are retried."""
        response_500 = DummyResponseWithStatus(500, payload={})
        response_ok = DummyResponseWithStatus(200, payload={"data": "success"})

        client = ClientWithRetryableError(response_500, response_ok, num_errors=1)

        def fake_client_factory(*, timeout):
            return client

        monkeypatch.setattr("app.riot.riotApiClient.httpx.Client", fake_client_factory)
        monkeypatch.setattr("app.riot.riotApiClient.time.sleep", lambda x: None)

        api_client = RiotApiClient(api_key="test-key", regional_routing="europe", max_retries=3)
        result = api_client.get_match_info_by_match_id("EUW1_123")

        assert result == {"data": "success"}
        assert client.call_count == 2

    def test_http_500_exceeds_max_retries_raises_error(self, monkeypatch):
        """Test that 500 errors that exceed max_retries raise the error."""
        response_500 = DummyResponseWithStatus(500, payload={})

        client = ClientWithException(response_500)

        def fake_client_factory(*, timeout):
            return client

        monkeypatch.setattr("app.riot.riotApiClient.httpx.Client", fake_client_factory)
        monkeypatch.setattr("app.riot.riotApiClient.time.sleep", lambda x: None)

        api_client = RiotApiClient(api_key="test-key", regional_routing="europe", max_retries=1)

        with pytest.raises(httpx.HTTPStatusError):
            api_client.get_match_info_by_match_id("EUW1_123")

    def test_http_404_client_error_does_not_retry(self, monkeypatch):
        """Test that client errors (400-499) are not retried."""
        response_404 = DummyResponseWithStatus(404, payload={})

        client = ClientWithException(response_404)

        def fake_client_factory(*, timeout):
            return client

        monkeypatch.setattr("app.riot.riotApiClient.httpx.Client", fake_client_factory)

        api_client = RiotApiClient(api_key="test-key", regional_routing="europe", max_retries=3)

        with pytest.raises(httpx.HTTPStatusError):
            api_client.get_match_info_by_match_id("EUW1_123")

        # Only called once (no retry for 404)
        assert client.call_count == 1


    def test_request_error_network_failure_retries(self, monkeypatch):
        """Test that network RequestErrors are retried."""
        call_count = [0]

        def fake_client_factory(*, timeout):
            class ClientRaisesError:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

                def get(self, url, headers=None, params=None):
                    call_count[0] += 1
                    if call_count[0] < 2:
                        raise httpx.RequestError("Connection refused")
                    response = DummyResponseWithStatus(200, payload={"data": "success"})
                    return response

            return ClientRaisesError()

        monkeypatch.setattr("app.riot.riotApiClient.httpx.Client", fake_client_factory)
        monkeypatch.setattr("app.riot.riotApiClient.time.sleep", lambda x: None)

        api_client = RiotApiClient(api_key="test-key", regional_routing="europe", max_retries=3)
        result = api_client.get_match_info_by_match_id("EUW1_123")

        assert result == {"data": "success"}
        assert call_count[0] == 2

    def test_request_error_exceeds_max_retries_raises(self, monkeypatch):
        """Test that RequestErrors exceeding max_retries are raised."""

        def fake_client_factory(*, timeout):
            class ClientRaisesError:
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc, tb):
                    return False

                def get(self, url, headers=None, params=None):
                    raise httpx.RequestError("Connection refused")

            return ClientRaisesError()

        monkeypatch.setattr("app.riot.riotApiClient.httpx.Client", fake_client_factory)
        monkeypatch.setattr("app.riot.riotApiClient.time.sleep", lambda x: None)

        api_client = RiotApiClient(api_key="test-key", regional_routing="europe", max_retries=1)

        with pytest.raises(httpx.RequestError):
            api_client.get_match_info_by_match_id("EUW1_123")

    def test_max_retries_configuration_used(self, monkeypatch):
        """Test that max_retries configuration is respected."""
        api_client = RiotApiClient(api_key="test-key", max_retries=5)
        assert api_client.max_retries == 5

    def test_special_tier_empty_response_list(self, monkeypatch):
        """Test special tier endpoints that return empty list."""
        response = DummyResponseWithStatus(200, payload={"entries": []})
        client = ClientWithException(response)

        def fake_client_factory(*, timeout):
            return client

        monkeypatch.setattr("app.riot.riotApiClient.httpx.Client", fake_client_factory)

        api_client = RiotApiClient(api_key="test-key", regional_routing="europe")
        result = api_client.get_league_entries("RANKED_SOLO_5x5", "CHALLENGER")

        assert result == []

    def test_special_tier_none_response_handled(self, monkeypatch):
        """Test special tier endpoints that return None as entries."""
        response = DummyResponseWithStatus(200, payload={"entries": None})
        client = ClientWithException(response)

        def fake_client_factory(*, timeout):
            return client

        monkeypatch.setattr("app.riot.riotApiClient.httpx.Client", fake_client_factory)

        api_client = RiotApiClient(api_key="test-key", regional_routing="europe")
        result = api_client.get_league_entries("RANKED_SOLO_5x5", "GRANDMASTER")

        # Current behavior: returns None when entries is None (not empty list)
        assert result is None
