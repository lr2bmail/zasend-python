# zasend

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](pyproject.toml)

Official Python client for the [zaSend](https://zasend.com) transactional email API.

zaSend is a developer-focused email delivery service for sending product, auth, billing, notification, and lifecycle emails from your application. This package is a small wrapper around the zaSend REST API for Python apps, Django, Flask, FastAPI, background jobs, and scripts.

Use it to:

- Send transactional email from verified domains
- Send template-based email with variables
- Check message status and events
- Manage suppressions, webhooks, templates, and domains
- Verify zaSend webhook signatures

The client stays close to the raw API. It has no heavy framework dependencies and uses `requests`.

## Install

```bash
pip install zasend
```

## Quick Start

```python
from zasend import ZaSend

client = ZaSend(api_key="sk_live_...")

result = client.send_email(
    from_email="zaSend <noreply@zasend.com>",
    to="user@example.com",
    subject="Welcome",
    text="Thanks for signing up.",
)

print(result["message_id"])
```

You can use an Account API Key (`sk_live_...`) for all methods. A Domain Sending Key (`dsk_live_...`) is restricted to sending email from one verified domain.

## Send HTML Email

```python
client.send_email(
    from_email="Acme <noreply@acme.com>",
    to="customer@example.com",
    subject="Your receipt",
    html="<h1>Thanks for your order</h1><p>Your receipt is attached.</p>",
    text="Thanks for your order. Your receipt is attached.",
)
```

## Send to Multiple Recipients

```python
client.send_email(
    from_email="Acme <noreply@acme.com>",
    to=["one@example.com", "two@example.com"],
    subject="Product update",
    text="A new update is available.",
)
```

zaSend returns one queued message per `to` recipient. Suppressed recipients reject the whole request so you can fix the list before sending.

## Template Send

```python
client.send_template_email(
    from_email="Acme <noreply@acme.com>",
    to="customer@example.com",
    template="welcome",
    variables={"name": "Ada"},
)
```

## Django Example

```python
# settings.py
ZASEND_API_KEY = "sk_live_..."

# anywhere in your app
from django.conf import settings
from zasend import ZaSend

zasend = ZaSend(settings.ZASEND_API_KEY)
zasend.send_email(
    from_email="Acme <noreply@acme.com>",
    to=user.email,
    subject="Reset your password",
    text="Use this link to reset your password.",
)
```

## Flask or FastAPI Example

```python
import os
from zasend import ZaSend

zasend = ZaSend(os.environ["ZASEND_API_KEY"])

def send_signup_email(email):
    return zasend.send_template_email(
        from_email="Acme <noreply@acme.com>",
        to=email,
        template="welcome",
        variables={"product": "Acme"},
    )
```

## Webhook Verification

zaSend signs webhook payloads with HMAC-SHA256. Verify the raw request body before trusting webhook data.

```python
from zasend import verify_webhook_signature

ok = verify_webhook_signature(
    request.get_data(),
    "whsec_...",
    request.headers.get("X-zaSend-Signature"),
)
```

## API Methods

| Method | Description |
| --- | --- |
| `send_email(**message)` | Send direct content or a template email |
| `send_template_email(...)` | Convenience wrapper for template sends |
| `get_email(message_id)` | Fetch email status and events |
| `get_rate_limits()` | Fetch daily usage and limits |
| `list_domains()` / `add_domain(domain)` / `verify_domain(id)` / `delete_domain(id)` | Manage sending domains |
| `list_suppressions(...)` / `add_suppression(email, ...)` / `delete_suppression(id)` | Manage suppression list entries |
| `list_webhooks()` / `create_webhook(url, events)` / `delete_webhook(id)` | Manage signed delivery webhooks |
| `list_templates()` / `create_template(...)` / `get_template(id)` / `update_template(id, ...)` / `delete_template(id)` | Manage email templates |

## Error Handling

```python
from zasend import APIError, RateLimitError, ValidationError, ZaSend

try:
    ZaSend("sk_live_...").send_email(
        from_email="Acme <noreply@acme.com>",
        to="user@example.com",
        subject="Hello",
        text="Body",
    )
except RateLimitError as exc:
    print("Rate limited:", exc)
except ValidationError as exc:
    print("Invalid request:", exc)
except APIError as exc:
    print("zaSend API error:", exc)
```

## Links

- Website: [zasend.com](https://zasend.com)
- API documentation: [zasend.com/docs](https://zasend.com/docs)
- Source: [GitHub](https://github.com/lr2bmail/zasend-python)

## License

MIT
