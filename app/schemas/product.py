from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# Subcategory schemas
class SubcategoryBase(BaseModel):
    name: str
    name_fr: Optional[str] = None
    description: Optional[str] = None
    description_fr: Optional[str] = None
    category_id: int
    image_url: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class SubcategoryCreate(SubcategoryBase):
    pass


class SubcategoryUpdate(BaseModel):
    name: Optional[str] = None
    name_fr: Optional[str] = None
    description: Optional[str] = None
    description_fr: Optional[str] = None
    category_id: Optional[int] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class Subcategory(SubcategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Enhanced Category schemas
class CategoryBase(BaseModel):
    name: str
    name_fr: Optional[str] = None
    description: Optional[str] = None
    description_fr: Optional[str] = None
    image_url: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    name_fr: Optional[str] = None
    description: Optional[str] = None
    description_fr: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class Category(CategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    subcategories: List[Subcategory] = []

    class Config:
        from_attributes = True


# Product Image schemas
class ProductImageBase(BaseModel):
    image_url: str
    alt_text: Optional[str] = None
    is_primary: bool = False
    sort_order: int = 0


class ProductImageCreate(ProductImageBase):
    pass


class ProductImageUpdate(ProductImageBase):
    image_url: Optional[str] = None
    is_primary: Optional[bool] = None
    sort_order: Optional[int] = None


class ProductImage(ProductImageBase):
    id: int
    product_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Inventory Movement schemas
class InventoryMovementBase(BaseModel):
    movement_type: str = Field(..., pattern="^(in|out|adjustment|reserved|released)$")
    quantity: int
    reason: Optional[str] = None
    reference_id: Optional[str] = None
    notes: Optional[str] = None


class InventoryMovementCreate(InventoryMovementBase):
    product_id: int


class InventoryMovement(InventoryMovementBase):
    id: int
    product_id: int
    created_by: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


# Product Variant schemas
class ProductVariantBase(BaseModel):
    sku: str
    size: Optional[str] = None
    color: Optional[str] = None
    stock_quantity: int = Field(0, ge=0)
    reserved_quantity: int = Field(0, ge=0)
    price_override: Optional[float] = Field(None, gt=0)
    is_active: bool = True


class ProductVariantCreate(ProductVariantBase):
    pass


class ProductVariantUpdate(ProductVariantBase):
    sku: Optional[str] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    reserved_quantity: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ProductVariant(ProductVariantBase):
    id: int
    product_id: int

    class Config:
        from_attributes = True


# Enhanced Product schemas
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    sale_price: Optional[float] = Field(None, gt=0)
    sku: str
    
    # Inventory fields
    stock_quantity: int = Field(0, ge=0)
    low_stock_threshold: int = Field(10, ge=0)
    reorder_level: int = Field(5, ge=0)
    max_stock_level: Optional[int] = Field(None, gt=0)
    reserved_quantity: int = Field(0, ge=0)
    
    # Category relationships
    category_id: int
    subcategory_id: Optional[int] = None
    
    # Product details
    brand: Optional[str] = None
    sizes: Optional[List[str]] = None  # Changed from single size to multiple sizes array
    color: Optional[str] = None
    material: Optional[str] = None
    weight: Optional[float] = Field(None, gt=0)
    dimensions: Optional[str] = None
    
    # Product image
    image_url: Optional[str] = None
    
    # Product status
    is_active: bool = True
    is_featured: bool = False
    is_digital: bool = False
    requires_shipping: bool = True
    
    # SEO and metadata
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    slug: Optional[str] = None
    
    # Pricing
    cost_price: Optional[float] = Field(None, gt=0)
    
    # Variants
    variants: Optional[List[ProductVariantCreate]] = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    sale_price: Optional[float] = Field(None, gt=0)
    sku: Optional[str] = None
    
    # Inventory fields
    stock_quantity: Optional[int] = Field(None, ge=0)
    low_stock_threshold: Optional[int] = Field(None, ge=0)
    reorder_level: Optional[int] = Field(None, ge=0)
    max_stock_level: Optional[int] = Field(None, gt=0)
    reserved_quantity: Optional[int] = Field(None, ge=0)
    
    # Category relationships
    category_id: Optional[int] = None
    subcategory_id: Optional[int] = None
    
    # Product details
    brand: Optional[str] = None
    sizes: Optional[List[str]] = None  # Changed from single size to multiple sizes array
    color: Optional[str] = None
    material: Optional[str] = None
    weight: Optional[float] = Field(None, gt=0)
    dimensions: Optional[str] = None
    
    # Product image
    image_url: Optional[str] = None
    
    # Product status
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_digital: Optional[bool] = None
    requires_shipping: Optional[bool] = None
    
    # SEO and metadata
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    slug: Optional[str] = None
    
    # Pricing
    cost_price: Optional[float] = Field(None, gt=0)
    
    # Variants (for update, usually handled separately but inclusive here)
    variants: Optional[List[ProductVariantCreate]] = None


class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_restocked: Optional[datetime] = None
    view_count: int = 0
    sales_count: int = 0
    
    # Relationships
    category: Optional[Category] = None
    subcategory: Optional[Subcategory] = None
    images: List[ProductImage] = []
    variants: List[ProductVariant] = []
    
    # Computed properties
    available_quantity: int
    is_low_stock: bool
    needs_reorder: bool
    profit_margin: Optional[float] = None

    class Config:
        from_attributes = True


class ProductListResponse(BaseModel):
    items: List[Product]
    total: int
    page: int
    per_page: int
    pages: int
    low_stock_count: int = 0
    needs_reorder_count: int = 0

    class Config:
        from_attributes = True


# Bulk operations schemas
class ProductImportRow(BaseModel):
    name: str
    description: Optional[str] = None
    price: float
    sale_price: Optional[float] = None
    sku: str
    stock_quantity: int = 0
    low_stock_threshold: int = 10
    reorder_level: int = 5
    category_name: str
    subcategory_name: Optional[str] = None
    brand: Optional[str] = None
    sizes: Optional[List[str]] = None  # Changed from single size to multiple sizes array
    color: Optional[str] = None
    material: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[str] = None
    cost_price: Optional[float] = None
    is_active: bool = True
    is_featured: bool = False


class ProductImportResponse(BaseModel):
    success_count: int
    error_count: int
    total_rows: int
    errors: List[str] = []
    created_products: List[int] = []  # Product IDs


class ProductExportRequest(BaseModel):
    include_inactive: bool = False
    category_ids: Optional[List[int]] = None
    format: str = Field("csv", pattern="^(csv|xlsx)$")


# Inventory alerts and reports
class InventoryAlert(BaseModel):
    product_id: int
    product_name: str
    sku: str
    current_stock: int
    threshold: int
    alert_type: str  # 'low_stock', 'needs_reorder', 'out_of_stock'
    days_until_stockout: Optional[int] = None


class InventoryReport(BaseModel):
    total_products: int
    active_products: int
    total_stock_value: float
    low_stock_alerts: List[InventoryAlert]
    reorder_alerts: List[InventoryAlert]
    out_of_stock_count: int
    categories_summary: List[dict] 