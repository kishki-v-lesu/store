import pytest
from decimal import Decimal

pytestmark = pytest.mark.asyncio


class TestDecimalPrecision:
    def test_product_price_decimal(self):
        from product_service.app.schemas.product import ProductCreate
        
        product = ProductCreate(
            name="Test Product",
            price=Decimal("99.99"),
            sku="TEST-001",
        )
        assert product.price == Decimal("99.99")

    def test_price_precision(self):
        from product_service.app.schemas.product import ProductCreate
        
        product = ProductCreate(
            name="Test Product",
            price=Decimal("0.01"),
            sku="TEST-001",
        )
        assert str(product.price) == "0.01"

    def test_large_price(self):
        from product_service.app.schemas.product import ProductCreate
        
        product = ProductCreate(
            name="Expensive Product",
            price=Decimal("999999.99"),
            sku="EXP-001",
        )
        assert product.price == Decimal("999999.99")


class TestOrderValidation:
    def test_order_item_positive_quantity(self):
        from order_service.app.schemas.order import OrderItemCreate
        
        item = OrderItemCreate(product_id=1, quantity=1)
        assert item.quantity == 1

    def test_order_item_zero_quantity_rejected(self):
        from pydantic import ValidationError
        from order_service.app.schemas.order import OrderItemCreate
        
        with pytest.raises(ValidationError):
            OrderItemCreate(product_id=1, quantity=0)

    def test_order_item_negative_quantity_rejected(self):
        from pydantic import ValidationError
        from order_service.app.schemas.order import OrderItemCreate
        
        with pytest.raises(ValidationError):
            OrderItemCreate(product_id=1, quantity=-5)


class TestPaymentValidation:
    def test_payment_decimal_amount(self):
        from payment_service.app.schemas.payment import PaymentCreate
        
        payment = PaymentCreate(
            order_id=1,
            amount=Decimal("149.99"),
            currency="USD",
        )
        assert payment.amount == Decimal("149.99")

    def test_payment_zero_amount_rejected(self):
        from pydantic import ValidationError
        from payment_service.app.schemas.payment import PaymentCreate
        
        with pytest.raises(ValidationError):
            PaymentCreate(
                order_id=1,
                amount=Decimal("0"),
                currency="USD",
            )

    def test_payment_currency_length(self):
        from pydantic import ValidationError
        from payment_service.app.schemas.payment import PaymentCreate
        
        with pytest.raises(ValidationError):
            PaymentCreate(
                order_id=1,
                amount=Decimal("99.99"),
                currency="USDD",
            )