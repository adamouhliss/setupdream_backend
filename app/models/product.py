from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    name_fr = Column(String, nullable=True) # French translation
    description = Column(Text, nullable=True)
    description_fr = Column(Text, nullable=True) # French translation
    image_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    subcategories = relationship("Subcategory", back_populates="category", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="category")


class Subcategory(Base):
    __tablename__ = "subcategories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    name_fr = Column(String, nullable=True) # French translation
    description = Column(Text, nullable=True)
    description_fr = Column(Text, nullable=True) # French translation
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    image_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    category = relationship("Category", back_populates="subcategories")
    products = relationship("Product", back_populates="subcategory")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    sale_price = Column(Float, nullable=True)
    sku = Column(String, unique=True, index=True, nullable=False)
    
    # Enhanced Inventory Management
    stock_quantity = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=10)  # Alert when below this
    reorder_level = Column(Integer, default=5)  # Suggest reorder when below this
    max_stock_level = Column(Integer, nullable=True)  # Maximum stock to maintain
    reserved_quantity = Column(Integer, default=0)  # Reserved for pending orders
    
    # Category relationships
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    subcategory_id = Column(Integer, ForeignKey("subcategories.id"), nullable=True)
    
    # Product details
    brand = Column(String, nullable=True)
    sizes = Column(JSON, nullable=True)  # Changed from single size to multiple sizes array
    color = Column(String, nullable=True)
    material = Column(String, nullable=True)
    weight = Column(Float, nullable=True)
    dimensions = Column(String, nullable=True)
    
    # Product image
    image_url = Column(String, nullable=True)  # Primary product image
    
    # Product status
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    is_digital = Column(Boolean, default=False)  # For digital products
    requires_shipping = Column(Boolean, default=True)
    
    # SEO and metadata
    meta_title = Column(String, nullable=True)
    meta_description = Column(Text, nullable=True)
    slug = Column(String, unique=True, nullable=True)  # URL-friendly name
    
    # Pricing and cost tracking
    cost_price = Column(Float, nullable=True)  # For profit margin calculations
    
    # Tracking
    view_count = Column(Integer, default=0)  # Product page views
    sales_count = Column(Integer, default=0)  # Number of times sold
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_restocked = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    category = relationship("Category", back_populates="products")
    subcategory = relationship("Subcategory", back_populates="products")
    images = relationship("ProductImage", back_populates="product", cascade="all, delete-orphan")
    cart_items = relationship("CartItem", back_populates="product")
    inventory_movements = relationship("InventoryMovement", back_populates="product", cascade="all, delete-orphan")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")

    @property
    def available_quantity(self):
        """Calculate available quantity (stock - reserved)"""
        return max(0, self.stock_quantity - self.reserved_quantity)
    
    @property
    def is_low_stock(self):
        """Check if product is below low stock threshold"""
        return self.stock_quantity <= self.low_stock_threshold
    
    @property
    def needs_reorder(self):
        """Check if product needs reordering"""
        return self.stock_quantity <= self.reorder_level
    
    @property
    def profit_margin(self):
        """Calculate profit margin if cost price is available"""
        if self.cost_price and self.price:
            return ((self.price - self.cost_price) / self.price) * 100
        return None


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    movement_type = Column(String, nullable=False)  # 'in', 'out', 'adjustment', 'reserved', 'released'
    quantity = Column(Integer, nullable=False)  # Positive for additions, negative for subtractions
    reason = Column(String, nullable=True)  # 'sale', 'restock', 'damage', 'return', etc.
    reference_id = Column(String, nullable=True)  # Order ID, Purchase Order ID, etc.
    notes = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    product = relationship("Product", back_populates="inventory_movements")


class ProductImage(Base):
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    image_url = Column(String, nullable=False)
    alt_text = Column(String, nullable=True)
    is_primary = Column(Boolean, default=False)
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    product = relationship("Product", back_populates="images") 