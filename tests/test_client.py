import hashlib
import hmac

import pytest

from zasend import APIError, RateLimitError, ValidationError, ZaSend, ZaSendError, verify_webhook_signature


class Response:
    def __init__(self, body=None, status_code=200, ok=True, reason="OK"):
        self._body = body
        self.status_code = status_code
        self.ok = ok
        self.reason = reason

    def json(self):
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


class Session:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def request(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.response


def test_send_email_posts_json_with_bearer_auth():
    session = Session(Response({"success": True, "message_id": "msg_123"}))
    client = ZaSend("key", base_url="https://example.test/api/v1", session=session)

    result = client.send_email(
        **{
            "from": "noreply@example.com",
            "to": "user@example.com",
            "subject": "Hello",
            "text": "Body",
        }
    )

    args, kwargs = session.calls[0]
    assert args == ("POST", "https://example.test/api/v1/emails/send")
    assert kwargs["headers"]["Authorization"] == "Bearer key"
    assert kwargs["json"]["subject"] == "Hello"
    assert result["message_id"] == "msg_123"


def test_list_suppressions_sends_query_parameters():
    session = Session(Response({"suppressions": []}))
    client = ZaSend("key", base_url="https://example.test/api/v1", session=session)

    client.list_suppressions(page=2, per_page=100, reason="bounce")

    _, kwargs = session.calls[0]
    assert kwargs["params"] == {"page": 2, "per_page": 100, "reason": "bounce"}


def test_typed_errors():
    with pytest.raises(RateLimitError):
        ZaSend("key", session=Session(Response({"message": "slow down"}, 429, False))).get_rate_limits()

    with pytest.raises(ValidationError):
        ZaSend("key", session=Session(Response({"message": "bad email"}, 422, False))).send_email()

    with pytest.raises(APIError):
        ZaSend("key", session=Session(Response({"message": "missing"}, 404, False))).get_email("missing")


def test_delete_methods_return_none_for_204():
    client = ZaSend("key", session=Session(Response(None, 204, True)))

    assert client.delete_webhook("hook_123") is None


def test_webhook_signature_verification_accepts_valid_signature():
    body = b'{"event":"accepted_by_postfix"}'
    secret = "secret"
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    assert verify_webhook_signature(body, secret, "sha256={0}".format(signature))


def test_client_errors_still_behave_like_value_error():
    assert issubclass(APIError, ZaSendError)
    assert issubclass(RateLimitError, APIError)
    assert issubclass(ValidationError, APIError)
    assert issubclass(ZaSendError, ValueError)
