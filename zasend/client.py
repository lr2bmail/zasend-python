import hashlib
import hmac

import requests


DEFAULT_BASE_URL = "https://zasend.com/api/v1"


class ZaSendError(ValueError):
    """Base exception for zaSend client errors."""


class APIError(ZaSendError):
    """Raised when the zaSend API returns an error response."""

    def __init__(self, message, status_code=None, body=None):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


class RateLimitError(APIError):
    """Raised when the API returns 429."""


class ValidationError(APIError):
    """Raised when the API returns a validation-style error."""


class ZaSend:
    """Lightweight client for the zaSend API."""

    def __init__(self, api_key, base_url=None, timeout=10, session=None):
        if not api_key:
            raise ZaSendError("API key is required")
        self.api_key = api_key
        self.base_url = (base_url or DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()

    def send_email(self, **message):
        if "from_email" in message and "from" not in message:
            message["from"] = message.pop("from_email")
        return self._request("POST", "/emails/send", json=message)

    def send_template_email(
        self,
        from_email,
        to,
        template,
        variables=None,
        cc=None,
        bcc=None,
        list_unsubscribe=None,
        list_unsubscribe_post=None,
    ):
        return self.send_email(
            **{
                "from": from_email,
                "to": to,
                "template": template,
                "variables": variables or {},
                "cc": cc,
                "bcc": bcc,
                "list_unsubscribe": list_unsubscribe,
                "list_unsubscribe_post": list_unsubscribe_post,
            }
        )

    def get_email(self, message_id):
        return self._request("GET", "/emails/{0}".format(message_id))

    def get_rate_limits(self):
        return self._request("GET", "/rate-limits")

    def list_domains(self):
        return self._request("GET", "/domains")

    def add_domain(self, domain):
        return self._request("POST", "/domains", json={"domain": domain})

    def verify_domain(self, domain_id):
        return self._request("POST", "/domains/{0}/verify".format(domain_id))

    def delete_domain(self, domain_id):
        return self._request("DELETE", "/domains/{0}".format(domain_id))

    def list_suppressions(self, page=None, per_page=None, reason=None):
        return self._request(
            "GET",
            "/suppressions",
            params={"page": page, "per_page": per_page, "reason": reason},
        )

    def add_suppression(self, email, reason="manual", details=None):
        return self._request(
            "POST",
            "/suppressions",
            json={"email": email, "reason": reason, "details": details},
        )

    def delete_suppression(self, suppression_id):
        return self._request("DELETE", "/suppressions/{0}".format(suppression_id))

    def list_webhooks(self):
        return self._request("GET", "/webhooks")

    def create_webhook(self, url, events):
        return self._request("POST", "/webhooks", json={"url": url, "events": events})

    def delete_webhook(self, webhook_id):
        return self._request("DELETE", "/webhooks/{0}".format(webhook_id))

    def list_templates(self):
        return self._request("GET", "/templates")

    def create_template(self, **template):
        return self._request("POST", "/templates", json=template)

    def get_template(self, template_id):
        return self._request("GET", "/templates/{0}".format(template_id))

    def update_template(self, template_id, **template):
        return self._request("PUT", "/templates/{0}".format(template_id), json=template)

    def delete_template(self, template_id):
        return self._request("DELETE", "/templates/{0}".format(template_id))

    def _request(self, method, path, json=None, params=None):
        headers = {
            "Authorization": "Bearer {0}".format(self.api_key),
            "Accept": "application/json",
        }
        clean_params = {k: v for k, v in (params or {}).items() if v is not None}
        response = self._session.request(
            method,
            "{0}{1}".format(self.base_url, path),
            headers=headers,
            json={k: v for k, v in (json or {}).items() if v is not None} if json is not None else None,
            params=clean_params or None,
            timeout=self.timeout,
        )

        if response.status_code == 204:
            return None

        try:
            data = response.json()
        except ValueError as exc:
            if response.ok:
                raise APIError("API returned invalid JSON", response.status_code) from exc
            data = None

        if not response.ok:
            message = data.get("message") if isinstance(data, dict) else response.reason
            if response.status_code == 429:
                raise RateLimitError(message, response.status_code, data)
            if response.status_code in (400, 422):
                raise ValidationError(message, response.status_code, data)
            raise APIError("API error {0}: {1}".format(response.status_code, message), response.status_code, data)

        return data


def verify_webhook_signature(payload_body, secret, signature_header):
    received = (signature_header or "").replace("sha256=", "", 1)
    if isinstance(payload_body, str):
        payload_body = payload_body.encode()
    expected = hmac.new(secret.encode(), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received)
