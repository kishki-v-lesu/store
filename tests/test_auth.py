import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestAuthRegister:
    async def test_register_success(self, client: AsyncClient, test_user_data):
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == test_user_data["email"]
        assert data["username"] == test_user_data["username"]
        assert "id" in data
        assert "hashed_password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient, test_user_data):
        await client.post("/api/v1/auth/register", json=test_user_data)
        response = await client.post("/api/v1/auth/register", json=test_user_data)
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"]

    async def test_register_duplicate_username(self, client: AsyncClient, test_user_data):
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        duplicate_username_data = test_user_data.copy()
        duplicate_username_data["email"] = "different@example.com"
        
        response = await client.post("/api/v1/auth/register", json=duplicate_username_data)
        assert response.status_code == 409
        assert "taken" in response.json()["detail"]

    async def test_register_invalid_email(self, client: AsyncClient):
        invalid_data = {
            "email": "not-an-email",
            "username": "validuser",
            "password": "TestPass123!",
            "first_name": "Test",
            "last_name": "User",
        }
        response = await client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        invalid_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "123",
            "first_name": "Test",
            "last_name": "User",
        }
        response = await client.post("/api/v1/auth/register", json=invalid_data)
        assert response.status_code == 422


class TestAuthLogin:
    async def test_login_success(self, client: AsyncClient, test_user_data):
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        }
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_login_wrong_password(self, client: AsyncClient, test_user_data):
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        login_data = {
            "email": test_user_data["email"],
            "password": "wrongpassword",
        }
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        login_data = {
            "email": "nonexistent@example.com",
            "password": "anypassword",
        }
        response = await client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401


class TestAuthMe:
    async def test_get_me_unauthorized(self, client: AsyncClient):
        response = await client.get("/api/v1/auth/me")
        assert response.status_code == 403

    async def test_get_me_success(self, client: AsyncClient, test_user_data):
        await client.post("/api/v1/auth/register", json=test_user_data)
        
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"],
        }
        login_response = await client.post("/api/v1/auth/login", json=login_data)
        access_token = login_response.json()["access_token"]
        
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user_data["email"]


class TestHealthCheck:
    async def test_health_check(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"