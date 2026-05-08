from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.auth_deps import get_current_user
from app.core.elasticsearch import search_products, index_product, delete_product_from_index
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductListResponse, ProductResponse, ProductUpdate

router = APIRouter(prefix="/api/v1/products", tags=["products"])


@router.get("/", response_model=ProductListResponse)
async def list_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category_id: int | None = None,
    search: str | None = None,
    ids: str | None = Query(None, description="Comma-separated product IDs"),
    db: AsyncSession = Depends(get_db),
):
    """List products with pagination and filtering."""
    if search:
        try:
            products_data, total = await search_products(search, category_id, page, per_page)
            return ProductListResponse(
                items=[ProductResponse(**p) for p in products_data],
                total=total,
                page=page,
                per_page=per_page,
            )
        except Exception:
            pass

    query = select(Product).where(Product.is_active == True)

    if ids:
        id_list = [int(i.strip()) for i in ids.split(",") if i.strip().isdigit()]
        query = query.where(Product.id.in_(id_list))
    
    elif category_id:
        query = query.where(Product.category_id == category_id)
    
    if search:
        safe_search = "".join(c for c in search if c.isalnum() or c in " -_")
        query = query.where(Product.name.ilike(f"%{safe_search}%"))

    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    products = result.scalars().all()

    return ProductListResponse(
        items=[ProductResponse.model_validate(p) for p in products],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single product by ID."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Create a new product."""
    product = Product(**product_data.model_dump(), user_id=current_user["id"])
    db.add(product)
    await db.flush()
    await db.refresh(product)
    await db.commit()
    
    try:
        await index_product(product.id, {
            "name": product.name,
            "description": product.description,
            "price": float(product.price),
            "category_id": product.category_id,
            "sku": product.sku,
            "stock_quantity": product.stock_quantity,
            "is_active": product.is_active,
        })
    except Exception:
        pass
    
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Update a product."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not your product")

    for key, value in product_data.model_dump(exclude_unset=True).items():
        setattr(product, key, value)

    await db.flush()
    await db.refresh(product)
    await db.commit()
    
    try:
        await index_product(product.id, {
            "name": product.name,
            "description": product.description,
            "price": float(product.price),
            "category_id": product.category_id,
            "sku": product.sku,
            "stock_quantity": product.stock_quantity,
            "is_active": product.is_active,
        })
    except Exception:
        pass
    
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a product."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if product.user_id != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not your product")

    await db.delete(product)
    await db.commit()
    
    try:
        await delete_product_from_index(product_id)
    except Exception:
        pass


@router.patch("/{product_id}/stock", response_model=ProductResponse)
async def update_stock(
    product_id: int,
    stock_change: int,
    db: AsyncSession = Depends(get_db),
):
    """Update product stock quantity (for order service)."""
    result = await db.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_stock = product.stock_quantity + stock_change
    if new_stock < 0:
        raise HTTPException(status_code=400, detail="Insufficient stock")

    product.stock_quantity = new_stock
    await db.flush()
    await db.refresh(product)
    await db.commit()
    return product
