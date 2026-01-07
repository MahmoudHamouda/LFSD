import requests

AUTH0_DOMAIN = "dev-lmc05ou12e7ep05p.eu.auth0.com"
AUTH0_CLIENT_ID = "VVw94DZQITVcARsNlp4JEZkyzMjsgioF"
AUTH0_CLIENT_SECRET = "vfMd6SgVMU3HYeQvFvjU4Au0i2mbpHYR_lepVuDYvdepslGRyQR1AS235hsqcHMj"

url = f"https://{AUTH0_DOMAIN}/oauth/token"
payload = {
    "grant_type": "http://auth0.com/oauth/grant-type/password-realm",
    "realm": "Username-Password-Authentication",
    "username": "finance@helm.com",
    "password": "P@ssword123",
    "client_id": AUTH0_CLIENT_ID,
    "client_secret": AUTH0_CLIENT_SECRET,
    "scope": "openid profile email offline_access"
}

print(f"Testing Login to {AUTH0_DOMAIN}...")
try:
    resp = requests.post(url, json=payload)
    print(f"Status Code: {resp.status_code}")
    print("Response JSON:")
    print(resp.json())
except Exception as e:
    print(f"Request Failed: {e}")
