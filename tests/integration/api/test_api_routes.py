from fastapi.testclient import TestClient
from app import create_app

app = create_app()
client = TestClient(app)



def test_history_flow():
    # 1. Generate (Start new chat)
    response = client.post("/history/generate", json={
        "messages": [
            {"id": "1", "role": "user", "content": "History Test", "date": "2023-01-01"}
        ]
    })
    assert response.status_code == 200
    data = response.json()
    conv_id = data["history_metadata"]["conversation_id"]
    assert conv_id is not None

    # 2. List
    response = client.get("/history/list")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    assert data[0]["id"] == conv_id

    # 3. Read
    response = client.post("/history/read", json={"conversation_id": conv_id})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conv_id
    assert len(data["messages"]) >= 2 # User msg + Echo

    # 4. Delete
    response = client.request("DELETE", "/history/delete", json={"conversation_id": conv_id})
    assert response.status_code == 200
    
    # 5. Verify Delete
    response = client.post("/history/read", json={"conversation_id": conv_id})
    assert response.status_code == 200
    assert response.json()["messages"] == []
