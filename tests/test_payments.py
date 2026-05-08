import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestPaymentsCreate:
    async def test_create_payment_unauthorized(self):
        from payment_service.app.main import app
        from httpx import ASGITransport
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payment_data = {
                "order_id": 1,
                "amount": 99.99,
                "currency": "USD",
            }
            response = await client.post("/api/v1/payments/", json=payment_data)
            assert response.status_code == 403


class TestPaymentValidation:
    async def test_create_payment_negative_amount(self):
        from payment_service.app.main import app
        from httpx import ASGITransport
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payment_data = {
                "order_id": 1,
                "amount": -10,
                "currency": "USD",
            }
            response = await client.post("/api/v1/payments/", json=payment_data)
            assert response.status_code == 422

    async def test_create_payment_zero_amount(self):
        from payment_service.app.main import app
        from httpx import ASGITransport
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payment_data = {
                "order_id": 1,
                "amount": 0,
                "currency": "USD",
            }
            response = await client.post("/api/v1/payments/", json=payment_data)
            assert response.status_code == 422


class TestWebhook:
    async def test_webhook_invalid_payload(self):
        from payment_service.app.main import app
        from httpx import ASGITransport
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/payments/webhook",
                content="invalid json",
                headers={"stripe-signature": "test_sig"}
            )
            assert response.status_code == 400


class TestHealthCheck:
    async def test_health_check(self):
        from payment_service.app.main import app
        from httpx import ASGITransport
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"

    async def test_readiness_check(self):
        from payment_service.app.main import app
        from httpx import ASGITransport
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/ready")
            assert response.status_code == 200
            assert response.json()["status"] == "ready"