from unittest.mock import MagicMock

from app.core.rate_limit import api_key_or_ip


def test_api_key_or_ip_prefers_api_key_header():
    request = MagicMock()
    request.headers = {"X-API-Key": "jp_test_token"}
    assert api_key_or_ip(request) == "api:jp_test_token"


def test_api_key_or_ip_falls_back_to_client_ip():
    request = MagicMock()
    request.headers = {}
    request.client.host = "203.0.113.10"
    assert api_key_or_ip(request) == "ip:203.0.113.10"
