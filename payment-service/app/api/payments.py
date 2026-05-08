import logging
import fastapi
import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.event_publisher import publish_event
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentCreate, PaymentResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payments", tags=["payments"])

stripe.api_key = settings.STRIPE_SECRET_KEY


@router.post("/", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED)
async def create_payment(
    payment_data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new payment."""
    idempotency_key = str(uuid.uuid4())
    
    payment = Payment(
        order_id=payment_data.order_id,
        user_id=current_user["id"],
        amount=payment_data.amount,
        currency=payment_data.currency,
        payment_method=payment_data.payment_method,
    )

    db.add(payment)
    await db.flush()

    try:
        intent = stripe.PaymentIntent.create(
            amount=int(float(payment_data.amount) * 100),
            currency=payment_data.currency.lower(),
            payment_method_types=["card"],
            idempotency_key=idempotency_key,
            metadata={
                "order_id": str(payment.order_id),
                "payment_id": str(payment.id),
            },
        )
        payment.stripe_payment_intent_id = intent.id
        payment.status = PaymentStatus.SUCCEEDED
    except stripe.error.StripeError as e:
        payment.status = PaymentStatus.FAILED
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Stripe error: {str(e)}",
        )

    await db.flush()
    await db.refresh(payment)
    await db.commit()

    await publish_event(
        "notifications",
        "notification.payment_succeeded",
        {
            "type": "payment_succeeded",
            "payment_id": payment.id,
            "order_id": payment.order_id,
            "user_id": payment.user_id,
            "email": current_user.get("email", ""),
            "amount": str(payment.amount),
        },
    )

    return payment


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get payment by ID."""
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return payment


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Handle Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "payment_intent.succeeded":
        intent = event["data"]["object"]
        result = await db.execute(
            select(Payment).where(Payment.stripe_payment_intent_id == intent["id"])
        )
        payment = result.scalar_one_or_none()
        if payment:
            payment.status = PaymentStatus.SUCCEEDED
            await db.flush()
            await db.commit()

            await publish_event(
                "notifications",
                "notification.payment_succeeded",
                {
                    "type": "payment_succeeded",
                    "payment_id": payment.id,
                    "order_id": payment.order_id,
                    "user_id": payment.user_id,
                    "amount": str(payment.amount),
                },
            )

    elif event["type"] == "payment_intent.payment_failed":
        intent = event["data"]["object"]
        result = await db.execute(
            select(Payment).where(Payment.stripe_payment_intent_id == intent["id"])
        )
        payment = result.scalar_one_or_none()
        if payment:
            payment.status = PaymentStatus.FAILED
            await db.flush()
            await db.commit()

    return {"status": "success"}
