from zasend import ZaSend


client = ZaSend(api_key="sk_live_...")

result = client.send_template_email(
    from_email="zaSend <noreply@zasend.com>",
    to="user@example.com",
    template="welcome",
    variables={"name": "Ada"},
)

print(result)
