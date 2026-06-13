from zasend import ZaSend


client = ZaSend(api_key="sk_live_...")

result = client.send_email(
    **{
        "from": "zaSend <noreply@zasend.com>",
        "to": "user@example.com",
        "subject": "Hello from zaSend",
        "text": "This message was sent with the zaSend Python client.",
    }
)

print(result)
