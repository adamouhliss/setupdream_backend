from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from ..core.database import Base

class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    
    sku = Column(String, unique=True, index=True, nullable=False)
    size = Column(String, nullable=True)
    color = Column(String, nullable=True)
    
    stock_quantity = Column(Integer, default=0)
    reserved_quantity = Column(Integer, default=0)
    
    price_override = Column(Float, nullable=True) # Optional override of base product price
    
    is_active = Column(Boolean, default=True)

    # Relationships
    product = relationship("Product", back_populates="variants")
    
    @property
    def available_quantity(self):
        return max(0, self.stock_quantity - self.reserved_quantity)
