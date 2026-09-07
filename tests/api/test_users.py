from fastapi.testclient import TestClient


def test_create_user_201(client: TestClient) -> None:
    payload = {
        "email": " Alice@Example.com",
        "password": "strongPassword01!",
    }
    response = client.post(url="/api/users/", json=payload)
    assert response.status_code == 201

    body = response.json()
    assert body["email"] == "alice@example.com"
    assert "id" in body
    assert "created_at" in body
    assert "password" not in body
    assert "hashed_password" not in body


def test_duplicate_email_409(client: TestClient) -> None:
    payload = {
        "email": "alice@example.com",
        "password": "strongPassword01!",
    }
    response = client.post(url="/api/users/", json=payload)
    assert response.status_code == 201
    response = client.post(url="/api/users/", json=payload)
    assert response.status_code == 409


def test_short_password_422(client: TestClient) -> None:
    payload = {
        "email": "bob@example.com",
        "password": "short",
    }
    response = client.post(url="/api/users/", json=payload)
    assert response.status_code == 422
