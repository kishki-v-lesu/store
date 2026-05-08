import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestProductsList:
    async def test_list_products_empty(self):
        from product_service.app.main import app
        from httpx import ASGITransport
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/products/")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "total" in data
            assert "page" in data
            assert "per_page" in data

    async def test_list_products_pagination(self):
        from product_service.app.main import app
        from httpx import ASGITransport
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/products/?page=1&per_page=5")
            assert response.status_code == 200
            data = response.json()
            assert data["per_page"] == 5

    @pytest.mark.parametrize("per_page,expected_code", [
        (50, 200),
        (101, 422),
    ])
    async def test_list_products_per_page_limits(self, per_page, expected_code):
        from product_service.app.main import app
        from httpx import ASGITransport
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/api/v1/products/?per_page={per_page}")
            assert response.status_code == expected_code


class TestProductCreate:
    async def test_create_product_unauthorized(self):
        from product_service.app.main import app
        from httpx import ASGITransport
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            product_data = {
                "name": "Test Product",
                "price": 99.99,
                "sku": "TEST-001",
            }
            response = await client.post("/api/v1/products/", json=product_data)
            assert response.status_code == 403


class TestProductValidation:
    async def test_create_product_negative_price(self):
        from product_service.app.main import app
        from httpx import ASGITransport
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            product_data = {
                "name": "Test Product",
                "price": -10,
                "sku": "TEST-001",
            }
            response = await client.post("/api/v1/products/", json=product_data)
            assert response.status_code == 422

    async def test_create_product_zero_price(self):
        from product_service.app.main import app
        from httpx import ASGITransport
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            product_data = {
                "name": "Test Product",
                "price": 0,
                "sku": "TEST-001",
            }
            response = await client.post("/api/v1/products/", json=product_data)
            assert response.status_code == 422

    async def test_create_product_negative_stock(self):
        from product_service.app.main import app
        from httpx import ASGITransport
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            product_data = {
                "name": "Test Product",
                "price": 99.99,
                "sku": "TEST-001",
                "stock_quantity": -5,
            }
            response = await client.post("/api/v1/products/", json=product_data)
            assert response.status_code == 422


class TestHealthCheck:
    async def test_health_check(self):
        from product_service.app.main import app
        from httpx import ASGITransport
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"

    async def test_readiness_check(self):
        from product_service.app.main import app
        from httpx import ASGITransport
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/ready")
            assert response.status_code == 200
            assert response.json()["status"] == "ready"