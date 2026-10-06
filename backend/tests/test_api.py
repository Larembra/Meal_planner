import pytest


@pytest.mark.asyncio
async def test_auth_and_profile(client):
    response = await client.post("/api/v1/auth/register", json={"email": "a@example.com", "name": "А", "password": "password123"})
    assert response.status_code == 201
    tokens = await client.post("/api/v1/auth/login", json={"email": "a@example.com", "password": "password123"})
    assert tokens.status_code == 200
    headers = {"Authorization": f"Bearer {tokens.json()['access_token']}"}
    assert (await client.get("/api/v1/users/me", headers=headers)).status_code == 200


@pytest.mark.asyncio
async def test_protected_resources(client):
    assert (await client.get("/api/v1/recipes")).status_code == 401
