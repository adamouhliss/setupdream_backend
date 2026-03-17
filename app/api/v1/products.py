from typing import List, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import io
import json

from ...api.deps import get_db, get_current_active_superuser, get_current_user_or_none
from ...crud.product import product_crud, category_crud, subcategory_crud, inventory_movement_crud
from ...schemas.product import (
    Product, ProductCreate, ProductUpdate, ProductListResponse,
    Category, CategoryCreate, CategoryUpdate,
    Subcategory, SubcategoryCreate, SubcategoryUpdate,
    InventoryMovement, InventoryMovementCreate,
    ProductImportResponse, ProductExportRequest,
    InventoryAlert, InventoryReport
)
from ...services.bulk_operations import bulk_operations_service
from ...services.image_service import image_service
from ...models.user import User
from ...models.product import ProductImage, Product as ProductModel, Category as CategoryModel
from sqlalchemy.orm import joinedload
from sqlalchemy import func

router = APIRouter()

# Category endpoints
@router.get("/categories/", response_model=List[Category])
def get_categories(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """Get all categories (public endpoint)"""
    categories = category_crud.get_multi(db, skip=skip, limit=limit, is_active=is_active)
    return categories

@router.post("/categories/", response_model=Category)
def create_category(
    *,
    db: Session = Depends(get_db),
    category_in: CategoryCreate,
    current_user: User = Depends(get_current_active_superuser)
):
    """Create new category (admin only)"""
    # Check if category name already exists
    existing_category = category_crud.get_by_name(db, name=category_in.name)
    if existing_category:
        raise HTTPException(
            status_code=400,
            detail="Category with this name already exists"
        )
    
    category = category_crud.create(db=db, obj_in=category_in)
    return category

@router.put("/categories/{category_id}", response_model=Category)
def update_category(
    *,
    db: Session = Depends(get_db),
    category_id: int,
    category_in: CategoryUpdate,
    current_user: User = Depends(get_current_active_superuser)
):
    """Update category (admin only)"""
    category = category_crud.get(db=db, id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    category = category_crud.update(db=db, db_obj=category, obj_in=category_in)
    return category

@router.delete("/categories/{category_id}")
def delete_category(
    *,
    db: Session = Depends(get_db),
    category_id: int,
    current_user: User = Depends(get_current_active_superuser)
):
    """Delete category (admin only)"""
    category = category_crud.get(db=db, id=category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check if category has products
    products_count = product_crud.get_count(db=db, category_id=category_id)
    if products_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete category with {products_count} products"
        )
    
    category_crud.remove(db=db, id=category_id)
    return {"message": "Category deleted successfully"}

# Product endpoints
@router.get("/", response_model=ProductListResponse)
def get_products(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    subcategory_id: Optional[int] = None,
    is_featured: Optional[bool] = None,
    search: Optional[str] = None,
    low_stock_only: bool = False,
    needs_reorder_only: bool = False,
    db: Session = Depends(get_db)
):
    """Get products with filtering"""
    products = product_crud.get_multi(
        db=db, 
        skip=skip, 
        limit=limit,
        category_id=category_id,
        subcategory_id=subcategory_id,
        is_featured=is_featured,
        search=search,
        low_stock_only=low_stock_only,
        needs_reorder_only=needs_reorder_only
    )
    
    total = product_crud.get_count(
        db=db,
        category_id=category_id,
        subcategory_id=subcategory_id,
        is_featured=is_featured,
        search=search,
        low_stock_only=low_stock_only,
        needs_reorder_only=needs_reorder_only
    )
    
    # Get inventory alerts counts
    low_stock_count = product_crud.get_count(db=db, low_stock_only=True)
    needs_reorder_count = product_crud.get_count(db=db, needs_reorder_only=True)
    
    pages = (total + limit - 1) // limit
    
    return ProductListResponse(
        items=products,
        total=total,
        page=(skip // limit) + 1,
        per_page=limit,
        pages=pages,
        low_stock_count=low_stock_count,
        needs_reorder_count=needs_reorder_count
    )

@router.get("/{product_id}", response_model=Product)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_or_none)
):
    """Get single product"""
    product = product_crud.get(db=db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Increment view count if user is not admin
    if current_user is None or not current_user.is_superuser:
        product.view_count += 1
        db.commit()
    
    return product

@router.post("/", response_model=Product)
async def create_product(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    # Form fields
    name: str = Form(...),
    description: str = Form(""),
    price: float = Form(...),
    sale_price: Optional[float] = Form(None),
    sku: str = Form(...),
    stock_quantity: int = Form(...),
    category_id: int = Form(...),
    subcategory_id: Optional[int] = Form(None),
    brand: str = Form(""),
    sizes: str = Form("[]"),  # Changed to receive as JSON string
    color: str = Form(""),
    material: str = Form(""),
    weight: Optional[float] = Form(None),
    dimensions: str = Form(""),
    is_active: bool = Form(True),
    is_featured: bool = Form(False),
    variants: str = Form("[]"),  # JSON string for variants
    # Image file
    image: Optional[UploadFile] = File(None)
):
    """Create new product with optional image (admin only)"""
    
    # Parse sizes JSON string
    try:
        sizes_list = json.loads(sizes) if sizes else []
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid sizes format")
    
    # Check if SKU already exists
    existing_product = product_crud.get_by_sku(db, sku=sku)
    if existing_product:
        raise HTTPException(
            status_code=400,
            detail="Product with this SKU already exists"
        )
    
    # Verify category exists
    category = category_crud.get(db=db, id=category_id)
    if not category:
        raise HTTPException(status_code=400, detail="Category not found")
    
    # Handle image upload
    image_url = None
    if image:
        image_url = await image_service.save_product_image(image)
    
    # Parse variants JSON string
    try:
        variants_list = json.loads(variants) if variants else []
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid variants format")

    # Create product data
    product_data = ProductCreate(
        name=name,
        description=description,
        price=price,
        sale_price=sale_price,
        sku=sku,
        stock_quantity=stock_quantity,
        category_id=category_id,
        subcategory_id=subcategory_id,
        brand=brand,
        sizes=sizes_list if sizes_list else None,  # Use parsed sizes list
        color=color,
        material=material,
        weight=weight,
        dimensions=dimensions,
        is_active=is_active,
        is_featured=is_featured,
        variants=variants_list
    )
    
    product = product_crud.create(db=db, obj_in=product_data)
    
    # Set image URL if uploaded and create ProductImage entry
    if image_url:
        # Set the primary image_url field for backward compatibility
        product.image_url = image_url
        
        # Create entry in product_images table
        product_image = ProductImage(
            product_id=product.id,
            image_url=image_url,
            alt_text=f"{product.name} - Primary Image",
            is_primary=True,
            sort_order=1
        )
        db.add(product_image)
        db.commit()
        db.refresh(product)
    
    # Record initial stock movement if there's initial stock
    if stock_quantity > 0:
        movement = InventoryMovementCreate(
            product_id=product.id,
            movement_type="in",
            quantity=stock_quantity,
            reason="initial_stock",
            notes="Initial stock on product creation"
        )
        inventory_movement_crud.create(db=db, obj_in=movement)
    
    return product

@router.put("/{product_id}", response_model=Product)
async def update_product(
    *,
    db: Session = Depends(get_db),
    product_id: int,
    current_user: User = Depends(get_current_active_superuser),
    # Form fields (all optional for updates)
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    price: Optional[float] = Form(None),
    sale_price: Optional[float] = Form(None),
    sku: Optional[str] = Form(None),
    stock_quantity: Optional[int] = Form(None),
    category_id: Optional[int] = Form(None),
    subcategory_id: Optional[int] = Form(None),
    brand: Optional[str] = Form(None),
    sizes: Optional[str] = Form(None),  # Changed to receive as JSON string
    color: Optional[str] = Form(None),
    material: Optional[str] = Form(None),
    weight: Optional[float] = Form(None),
    dimensions: Optional[str] = Form(None),
    is_active: Optional[bool] = Form(None),
    is_featured: Optional[bool] = Form(None),
    variants: Optional[str] = Form(None),  # JSON string for variants
    # Image file
    image: Optional[UploadFile] = File(None)
):
    """Update product with optional image (admin only)"""
    
    # Parse sizes JSON string if provided
    sizes_list = None
    if sizes is not None:
        try:
            sizes_list = json.loads(sizes) if sizes else []
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid sizes format")
    
    product = product_crud.get(db=db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check SKU uniqueness if being updated
    if sku and sku != product.sku:
        existing_product = product_crud.get_by_sku(db, sku=sku)
        if existing_product:
            raise HTTPException(
                status_code=400,
                detail="Product with this SKU already exists"
            )
    
    # Verify category exists if being updated
    if category_id:
        category = category_crud.get(db=db, id=category_id)
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
    
    # Handle image upload
    if image:
        # Delete old image if exists
        if product.image_url:
            image_service.delete_image(product.image_url)
        
        # Upload new image
        image_url = await image_service.save_product_image(image)
        
        # Update product with new image URL
        product.image_url = image_url
        
        # Update or create ProductImage entry
        existing_primary_image = db.query(ProductImage).filter(
            ProductImage.product_id == product_id,
            ProductImage.is_primary == True
        ).first()
        
        if existing_primary_image:
            # Update existing primary image
            existing_primary_image.image_url = image_url
            existing_primary_image.alt_text = f"{product.name} - Primary Image"
        else:
            # Create new primary image entry
            product_image = ProductImage(
                product_id=product_id,
                image_url=image_url,
                alt_text=f"{product.name} - Primary Image",
                is_primary=True,
                sort_order=1
            )
            db.add(product_image)
    
    # Parse variants JSON string if provided
    variants_list = None
    if variants is not None:
        try:
            variants_list = json.loads(variants) if variants else []
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid variants format")

    # Create update data from form fields
    update_data = {}
    form_fields = {
        'name': name, 'description': description, 'price': price, 'sale_price': sale_price,
        'sku': sku, 'stock_quantity': stock_quantity, 'category_id': category_id,
        'subcategory_id': subcategory_id, 'brand': brand, 'sizes': sizes_list, 'color': color,  # Use parsed sizes_list
        'material': material, 'weight': weight, 'dimensions': dimensions,
        'is_active': is_active, 'is_featured': is_featured,
        'variants': variants_list
    }
    
    for field, value in form_fields.items():
        if value is not None:
            update_data[field] = value
    
    # Track stock changes
    old_stock = product.stock_quantity
    
    # Update product
    updated_product = product_crud.update(db=db, db_obj=product, obj_in=update_data)
    
    # Record stock movement if quantity changed
    if stock_quantity is not None and stock_quantity != old_stock:
        quantity_change = stock_quantity - old_stock
        movement = InventoryMovementCreate(
            product_id=product_id,
            movement_type="adjustment",
            quantity=quantity_change,
            reason="manual_adjustment",
            notes=f"Stock adjusted by admin from {old_stock} to {stock_quantity}"
        )
        inventory_movement_crud.create(db=db, obj_in=movement)
    
    return updated_product

@router.delete("/{product_id}")
def delete_product(
    *,
    db: Session = Depends(get_db),
    product_id: int,
    current_user: User = Depends(get_current_active_superuser)
):
    """Delete product (admin only)"""
    product = product_crud.get(db=db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product_crud.remove(db=db, id=product_id)
    return {"message": "Product deleted successfully"}

@router.post("/{product_id}/toggle-featured")
def toggle_product_featured(
    *,
    db: Session = Depends(get_db),
    product_id: int,
    current_user: User = Depends(get_current_active_superuser)
):
    """Toggle product featured status (admin only)"""
    product = product_crud.get(db=db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.is_featured = not product.is_featured
    db.commit()
    db.refresh(product)
    
    return {"message": f"Product {'featured' if product.is_featured else 'unfeatured'} successfully"}

@router.post("/{product_id}/toggle-active")
def toggle_product_active(
    *,
    db: Session = Depends(get_db),
    product_id: int,
    current_user: User = Depends(get_current_active_superuser)
):
    """Toggle product active status (admin only)"""
    product = product_crud.get(db=db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product.is_active = not product.is_active
    db.commit()
    db.refresh(product)
    
    return {"message": f"Product {'activated' if product.is_active else 'deactivated'} successfully"}

# Admin-only endpoints
@router.get("/admin/all", response_model=ProductListResponse)
def get_all_products_admin(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    subcategory_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Get all products for admin (including inactive)"""
    products = product_crud.get_multi(
        db=db, 
        skip=skip, 
        limit=limit,
        category_id=category_id,
        subcategory_id=subcategory_id,
        is_active=is_active,
        search=search
    )
    
    total = product_crud.get_count(
        db=db,
        category_id=category_id,
        subcategory_id=subcategory_id,
        is_active=is_active,
        search=search
    )
    
    pages = (total + limit - 1) // limit
    
    return ProductListResponse(
        items=products,
        total=total,
        page=(skip // limit) + 1,
        per_page=limit,
        pages=pages
    )

# Subcategory endpoints
@router.get("/subcategories/", response_model=List[Subcategory])
def get_all_subcategories(
    is_active: Optional[bool] = None,
    category_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """Get all subcategories (optionally filter by category and active status)"""
    return subcategory_crud.get_all(db=db, is_active=is_active, category_id=category_id)

@router.get("/categories/{category_id}/subcategories/", response_model=List[Subcategory])
def get_subcategories(
    category_id: int,
    is_active: bool = True,
    db: Session = Depends(get_db)
):
    """Get subcategories for a category"""
    return subcategory_crud.get_by_category(db=db, category_id=category_id, is_active=is_active)

@router.post("/subcategories/", response_model=Subcategory)
def create_subcategory(
    subcategory_in: SubcategoryCreate,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Create new subcategory"""
    if subcategory_crud.get_by_name_and_category(
        db=db, 
        name=subcategory_in.name, 
        category_id=subcategory_in.category_id
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subcategory with this name already exists in this category"
        )
    
    return subcategory_crud.create(db=db, obj_in=subcategory_in)

@router.put("/subcategories/{subcategory_id}", response_model=Subcategory)
def update_subcategory(
    subcategory_id: int,
    subcategory_in: SubcategoryUpdate,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Update subcategory"""
    subcategory = subcategory_crud.get(db=db, id=subcategory_id)
    if not subcategory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subcategory not found"
        )
    
    return subcategory_crud.update(db=db, db_obj=subcategory, obj_in=subcategory_in)

@router.delete("/subcategories/{subcategory_id}")
def delete_subcategory(
    subcategory_id: int,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Delete subcategory"""
    subcategory = subcategory_crud.get(db=db, id=subcategory_id)
    if not subcategory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subcategory not found"
        )
    
    # Check if subcategory has products
    products_count = product_crud.get_count(db=db, subcategory_id=subcategory_id)
    if products_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete subcategory with {products_count} products"
        )
    
    subcategory_crud.remove(db=db, id=subcategory_id)
    return {"message": "Subcategory deleted successfully"}

# Inventory management endpoints
@router.get("/inventory/alerts", response_model=List[InventoryAlert])
def get_inventory_alerts(
    alert_type: Optional[str] = None,  # 'low_stock', 'needs_reorder', 'out_of_stock'
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Get inventory alerts"""
    alerts = []
    
    if alert_type in [None, 'low_stock']:
        low_stock_products = product_crud.get_low_stock_products(db=db, limit=limit)
        for product in low_stock_products:
            alerts.append(InventoryAlert(
                product_id=product.id,
                product_name=product.name,
                sku=product.sku,
                current_stock=product.stock_quantity,
                threshold=product.low_stock_threshold,
                alert_type='low_stock'
            ))
    
    if alert_type in [None, 'needs_reorder']:
        reorder_products = product_crud.get_reorder_products(db=db, limit=limit)
        for product in reorder_products:
            alerts.append(InventoryAlert(
                product_id=product.id,
                product_name=product.name,
                sku=product.sku,
                current_stock=product.stock_quantity,
                threshold=product.reorder_level,
                alert_type='needs_reorder'
            ))
    
    if alert_type in [None, 'out_of_stock']:
        out_of_stock_products = product_crud.get_out_of_stock_products(db=db, limit=limit)
        for product in out_of_stock_products:
            alerts.append(InventoryAlert(
                product_id=product.id,
                product_name=product.name,
                sku=product.sku,
                current_stock=0,
                threshold=0,
                alert_type='out_of_stock'
            ))
    
    return alerts

@router.get("/inventory/report", response_model=InventoryReport)
def get_inventory_report(
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Get comprehensive inventory report"""
    summary = product_crud.get_inventory_summary(db=db)
    
    # Get alerts
    low_stock_alerts = []
    low_stock_products = product_crud.get_low_stock_products(db=db, limit=50)
    for product in low_stock_products:
        low_stock_alerts.append(InventoryAlert(
            product_id=product.id,
            product_name=product.name,
            sku=product.sku,
            current_stock=product.stock_quantity,
            threshold=product.low_stock_threshold,
            alert_type='low_stock'
        ))
    
    reorder_alerts = []
    reorder_products = product_crud.get_reorder_products(db=db, limit=50)
    for product in reorder_products:
        reorder_alerts.append(InventoryAlert(
            product_id=product.id,
            product_name=product.name,
            sku=product.sku,
            current_stock=product.stock_quantity,
            threshold=product.reorder_level,
            alert_type='needs_reorder'
        ))
    
    return InventoryReport(
        total_products=summary["total_products"],
        active_products=summary["total_products"],  # All counted products are active
        total_stock_value=summary["total_stock_value"],
        low_stock_alerts=low_stock_alerts,
        reorder_alerts=reorder_alerts,
        out_of_stock_count=summary["out_of_stock_count"],
        categories_summary=[]  # Can be implemented later if needed
    )

@router.post("/{product_id}/stock")
def update_product_stock(
    product_id: int,
    quantity_change: int,
    movement_type: str,
    reason: Optional[str] = None,
    reference_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Update product stock and record movement"""
    try:
        product = product_crud.update_stock(
            db=db,
            product_id=product_id,
            quantity_change=quantity_change,
            movement_type=movement_type,
            reason=reason,
            reference_id=reference_id,
            user_id=current_user.id
        )
        return {"message": "Stock updated successfully", "new_quantity": product.stock_quantity}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

@router.get("/{product_id}/movements", response_model=List[InventoryMovement])
def get_product_movements(
    product_id: int,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Get inventory movements for a product"""
    return inventory_movement_crud.get_by_product(
        db=db, 
        product_id=product_id, 
        skip=skip, 
        limit=limit
    )

# Bulk operations endpoints
@router.post("/import/csv", response_model=ProductImportResponse)
async def import_products_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Import products from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a CSV file"
        )
    
    content = await file.read()
    csv_content = content.decode('utf-8')
    
    return bulk_operations_service.import_products_from_csv(
        db=db, 
        csv_content=csv_content,
        user_id=current_user.id
    )

@router.post("/import/excel", response_model=ProductImportResponse)
async def import_products_excel(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Import products from Excel file"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an Excel file (.xlsx or .xls)"
        )
    
    content = await file.read()
    
    return bulk_operations_service.import_products_from_excel(
        db=db, 
        excel_content=content,
        user_id=current_user.id
    )

@router.get("/export/template")
def download_import_template(
    current_user: User = Depends(get_current_active_superuser)
):
    """Download CSV template for product import"""
    template_content = bulk_operations_service.get_import_template()
    
    return StreamingResponse(
        io.StringIO(template_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=product_import_template.csv"}
    )

@router.post("/export/csv")
def export_products_csv(
    export_request: ProductExportRequest,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Export products to CSV"""
    csv_content = bulk_operations_service.export_products_to_csv(
        db=db,
        include_inactive=export_request.include_inactive,
        category_ids=export_request.category_ids
    )
    
    return StreamingResponse(
        io.StringIO(csv_content),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=products_export.csv"}
    )

@router.post("/export/excel")
def export_products_excel(
    export_request: ProductExportRequest,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Export products to Excel"""
    excel_content = bulk_operations_service.export_products_to_excel(
        db=db,
        include_inactive=export_request.include_inactive,
        category_ids=export_request.category_ids
    )
    
    return StreamingResponse(
        io.BytesIO(excel_content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=products_export.xlsx"}
    )

@router.post("/{product_id}/images", response_model=Product)
async def upload_product_images(
    product_id: int,
    images: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Upload multiple images for a product (max 3 images)"""
    product = product_crud.get(db=db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Validate number of images
    if len(images) > 3:
        raise HTTPException(
            status_code=400, 
            detail="Maximum 3 images allowed per product"
        )
    
    # Delete existing images
    existing_images = db.query(ProductImage).filter(ProductImage.product_id == product_id).all()
    for existing_image in existing_images:
        image_service.delete_image(existing_image.image_url)
        db.delete(existing_image)
    
    # Reset product image_url
    product.image_url = None
    
    # Upload new images
    uploaded_images = []
    for index, image in enumerate(images):
        # Upload image
        image_url = await image_service.save_product_image(image)
        
        # Create ProductImage entry
        product_image = ProductImage(
            product_id=product_id,
            image_url=image_url,
            alt_text=f"{product.name} - Image {index + 1}",
            is_primary=(index == 0),  # First image is primary
            sort_order=index + 1
        )
        db.add(product_image)
        uploaded_images.append(product_image)
        
        # Set first image as product's primary image for backward compatibility
        if index == 0:
            product.image_url = image_url
    
    db.commit()
    db.refresh(product)
    
    return product

@router.delete("/{product_id}/images/{image_id}")
def delete_product_image(
    product_id: int,
    image_id: int,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Delete a specific product image"""
    product = product_crud.get(db=db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Get the image
    product_image = db.query(ProductImage).filter(
        ProductImage.id == image_id,
        ProductImage.product_id == product_id
    ).first()
    
    if not product_image:
        raise HTTPException(status_code=404, detail="Product image not found")
    
    # Delete the image file
    image_service.delete_image(product_image.image_url)
    
    # If this was the primary image, update product.image_url
    if product_image.is_primary:
        product.image_url = None
        
        # Find another image to make primary
        other_image = db.query(ProductImage).filter(
            ProductImage.product_id == product_id,
            ProductImage.id != image_id
        ).order_by(ProductImage.sort_order).first()
        
        if other_image:
            other_image.is_primary = True
            product.image_url = other_image.image_url
    
    # Delete the database record
    db.delete(product_image)
    db.commit()
    db.refresh(product)
    
    return {"message": "Image deleted successfully"}

@router.post("/{product_id}/image", response_model=Product)
async def upload_product_image(
    product_id: int,
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db)
):
    """Upload an image for a product"""
    product = product_crud.get(db=db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Delete old image if exists
    if product.image_url:
        image_service.delete_image(product.image_url)
    
    # Upload new image
    image_url = await image_service.save_product_image(image)
    
    # Update product with new image URL
    product.image_url = image_url
    db.commit()
    db.refresh(product)
    
    return product

@router.patch("/{product_id}/bulk-update")
def bulk_update_product(
    *,
    db: Session = Depends(get_db),
    product_id: int,
    update_data: dict,
    current_user: User = Depends(get_current_active_superuser)
):
    """Bulk update product fields (admin only)"""
    product = product_crud.get(db=db, id=product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Apply updates
    for field, value in update_data.items():
        if hasattr(product, f"is_{field}"):
            setattr(product, f"is_{field}", value)
        elif hasattr(product, field):
            setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    return {"message": "Product updated successfully"} 

# XML Feed endpoints
@router.get("/xml-feed/")
def get_product_xml_feed(
    feed_type: str = "general",  # general, google, facebook
    include_inactive: bool = False,
    db: Session = Depends(get_db)
):
    """
    Generate XML product feed for various platforms
    - general: Basic XML feed with all required attributes
    - google: Google Shopping optimized feed 
    - facebook: Facebook Catalog optimized feed
    """
    from ...services.xml_feed_service import xml_feed_service
    
    try:
        if feed_type == "google":
            xml_content = xml_feed_service.generate_google_shopping_feed(db)
            filename = "google_shopping_feed.xml"
        elif feed_type == "facebook":
            xml_content = xml_feed_service.generate_facebook_catalog_feed(db)
            filename = "facebook_catalog_feed.xml"
        else:
            xml_content = xml_feed_service.generate_product_feed(db, include_inactive)
            filename = "product_feed.xml"
        
        # Return as downloadable file
        return StreamingResponse(
            io.BytesIO(xml_content.encode('utf-8')),
            media_type="application/xml",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating XML feed: {str(e)}"
        )

@router.get("/xml-feed/preview/")
def preview_product_xml_feed(
    feed_type: str = "general",
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Preview XML product feed (first few products only)
    Useful for testing and debugging
    """
    from ...services.xml_feed_service import xml_feed_service
    
    try:
        # Create a temporary service for preview with limited products
        class PreviewXMLService(xml_feed_service.__class__):
            def _get_products(self, db: Session, include_inactive: bool = False):
                query = db.query(ProductModel).options(
                    joinedload(Product.category),
                    joinedload(Product.subcategory),
                    joinedload(Product.images)
                ).filter(Product.is_active == True).limit(limit)
                
                return query.all()
        
        preview_service = PreviewXMLService()
        
        if feed_type == "google":
            xml_content = preview_service.generate_google_shopping_feed(db)
        elif feed_type == "facebook":
            xml_content = preview_service.generate_facebook_catalog_feed(db)
        else:
            xml_content = preview_service.generate_product_feed(db, False)
        
        return {"xml_preview": xml_content}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating XML preview: {str(e)}"
        )

@router.get("/xml-feed/stats/")
def get_xml_feed_stats(db: Session = Depends(get_db)):
    """Get statistics about products that would be included in XML feeds"""
    
    try:
        # Total products
        total_products = db.query(ProductModel).filter(Product.is_active == True).count()
        
        # Products with images
        products_with_images = db.query(ProductModel).filter(
            Product.is_active == True,
            Product.image_url.isnot(None)
        ).count()
        
        # Products by category
        category_stats = db.query(
            CategoryModel.name,
            func.count(Product.id).label('product_count')
        ).join(ProductModel).filter(
            Product.is_active == True
        ).group_by(CategoryModel.name).all()
        
        # In stock vs out of stock
        in_stock = db.query(ProductModel).filter(
            Product.is_active == True,
            Product.stock_quantity > 0
        ).count()
        
        out_of_stock = total_products - in_stock
        
        # Products with sale prices
        on_sale = db.query(ProductModel).filter(
            Product.is_active == True,
            Product.sale_price.isnot(None),
            Product.sale_price < Product.price
        ).count()
        
        return {
            "total_active_products": total_products,
            "products_with_images": products_with_images,
            "image_coverage_percentage": round((products_with_images / total_products * 100), 2) if total_products > 0 else 0,
            "in_stock": in_stock,
            "out_of_stock": out_of_stock,
            "products_on_sale": on_sale,
            "category_breakdown": [
                {"category": stat.name, "count": stat.product_count}
                for stat in category_stats
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error getting feed stats: {str(e)}"
        ) 
