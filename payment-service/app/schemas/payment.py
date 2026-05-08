from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.payment import PaymentStatus


class PaymentCreate(BaseModel):
    order_id: int
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(default="USD", max_length=3)
    payment_method: str = Field(default="card")


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    user_id: int
    amount: Decimal
    currency: str
    status: PaymentStatus
    payment_method: str
    stripe_payment_intent_id: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
