import requests

def test_financial_score():
    # Login as steward
    login_url = "http://localhost:8000/api/auth/token"
    # Note: Port 8000 for backend
    payload = {"username": "steward@helm.com", "password": "P@ssword123"}
    try:
        response = requests.post(login_url, data=payload)
        response.raise_for_status()
        token = response.json()["access_token"]
        print("Login successful.")

        # Get Scores
        score_url = "http://localhost:8000/api/scores/current?period=month"
        headers = {"Authorization": f"Bearer {token}"}
        score_resp = requests.get(score_url, headers=headers)
        score_resp.raise_for_status()
        data = score_resp.json()
        
        print(f"Overall Score: {data.get('overall', {}).get('score')}")
        print("Categories:")
        for k, v in data.get("categories", {}).items():
            print(f" - {k}: {v.get('score')}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_financial_score()
