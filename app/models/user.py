from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from ..core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String, nullable=True)
    postal_code = Column(String, nullable=True)
    country = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    has_used_first_time_discount = Column(Boolean, default=False)
    
    # Influencer / Affiliate System
    is_influencer = Column(Boolean, default=False)
    promo_code = Column(String, unique=True, index=True, nullable=True) # E.g., MOHAMMED10
    commission_rate = Column(Float, default=10.0) # Percentage the influencer earns
    customer_discount_rate = Column(Float, default=10.0) # Percentage the customer saves
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    orders = relationship("Order", back_populates="customer")
    cart_items = relationship("CartItem", back_populates="user") 