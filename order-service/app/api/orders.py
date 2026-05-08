from decimal import Decimal
import logging
from datetime import datetime, timezone
import httpx

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth_deps import get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.event_publisher import publish_event
from app.models.order import Order, OrderItem, OrderStatus
from app.schemas.order import OrderCreate, OrderListResponse, OrderResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

STOCK_RESERVED_KEY = "stock_reserved"


@router.get("/", response_model=OrderListResponse)
async def list_orders(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    status_filter: OrderStatus | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List orders with pagination."""
    query = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == current_user["id"])
    )
    if status_filter:
        query = query.where(Order.status == status_filter)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    orders = result.scalars().all()

    return OrderListResponse(
        items=[OrderResponse.model_validate(o) for o in orders],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get order by ID."""
    result = await db.execute(
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return OrderResponse.model_validate(order)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new order."""
    product_ids = [item.product_id for item in order_data.items]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.PRODUCT_SERVICE_URL}/api/v1/products/",
                params={"ids": product_ids},
                timeout=10.0,
            )
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to fetch product details")
            products_data = response.json()
            products = {p["id"]: p for p in products_data}
    except httpx.TimeoutException:
        raise HTTPException(status_code=503, detail="Product service unavailable")
    except httpx.RequestError:
        raise HTTPException(status_code=503, detail="Product service unavailable")

    reserved_products = []
    try:
        async with httpx.AsyncClient() as client:
            for item_data in order_data.items:
                product = products.get(item_data.product_id)
                if not product:
                    raise HTTPException(status_code=404, detail=f"Product {item_data.product_id} not found")
                
                if product["stock_quantity"] < item_data.quantity:
                    raise HTTPException(status_code=400, detail=f"Insufficient stock for product {product['name']}")
                
                resp = await client.patch(
                    f"{settings.PRODUCT_SERVICE_URL}/api/v1/products/{item_data.product_id}/stock",
                    json={"stock_change": -item_data.quantity},
                    timeout=10.0,
                )
                if resp.status_code != 200:
                    raise HTTPException(status_code=400, detail=f"Failed to reserve stock for product {item_data.product_id}")
                reserved_products.append(item_data)

        total_amount = Decimal("0")
        items = []
        for item_data in order_data.items:
            product = products.get(item_data.product_id)
            unit_price = Decimal(str(product["price"]))
            total_price = unit_price * item_data.quantity
            total_amount += total_price

            items.append(
                OrderItem(
                    product_id=item_data.product_id,
                    quantity=item_data.quantity,
                    unit_price=unit_price,
                    total_price=total_price,
                )
            )

        order = Order(
            user_id=current_user["id"],
            total_amount=total_amount,
            shipping_address=order_data.shipping_address,
            items=items,
        )

        db.add(order)
        await db.flush()
        await db.refresh(order)
        await db.commit()

        await publish_event(
            "notifications",
            "notification.order_created",
            {
                "type": "order_created",
                "order_id": order.id,
                "user_id": order.user_id,
                "email": current_user.get("email", ""),
                "total_amount": str(order.total_amount),
            },
        )

        return {
            "id": order.id,
            "user_id": order.user_id,
            "status": order.status,
            "total_amount": order.total_amount,
            "currency": order.currency,
            "shipping_address": order.shipping_address,
            "created_at": order.created_at,
        }

    except HTTPException:
        await rollback_stock_reservation(reserved_products, products)
        raise
    except Exception as e:
        logger.error(f"Failed to create order: {e}")
        await rollback_stock_reservation(reserved_products, products)
        raise HTTPException(status_code=500, detail="Failed to create order")


async def rollback_stock_reservation(reserved_products, products):
    """Rollback stock reservation on failure."""
    if not reserved_products:
        return
    try:
        async with httpx.AsyncClient() as client:
            for item_data in reserved_products:
                await client.patch(
                    f"{settings.PRODUCT_SERVICE_URL}/api/v1/products/{item_data.product_id}/stock",
                    json={"stock_change": item_data.quantity},
                    timeout=10.0,
                )
    except Exception as e:
        logger.error(f"Failed to rollback stock reservation: {e}")


@router.patch("/{order_id}/status", response_model=OrderResponse)
async def update_order_status(
    order_id: int,
    new_status: OrderStatus,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update order status."""
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not enough permissions")

    order.status = new_status
    await db.flush()
    await db.refresh(order)
    await db.commit()
    return order
