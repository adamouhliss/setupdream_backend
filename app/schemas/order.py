from typing import List, Optional, Any
from pydantic import BaseModel
from datetime import datetime


class OrderItemSchema(BaseModel):
    productId: int
    productName: str
    quantity: int
    price: float
    selectedColor: Optional[str] = None
    selectedSize: Optional[str] = None  # Added selectedSize field
    productImage: Optional[str] = None  # Added productImage field for order display
    total: float


class ShippingInfoSchema(BaseModel):
    firstName: str
    lastName: str
    email: str
    phone: str
    address: str
    city: str
    postalCode: str
    country: str


class OrderBase(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone: str
    address: str
    city: str
    postal_code: str
    country: str
    items: List[OrderItemSchema]
    payment_method: str = "cash"
    subtotal: float
    discount_amount: float = 0.0
    discount_code: Optional[str] = None
    shipping: float = 0.0
    tax: float = 0.0
    total: float
    status: str = "pending"
    notes: Optional[str] = None


class OrderCreate(OrderBase):
    customer_id: Optional[int] = None


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None


class OrderResponse(BaseModel):
    id: int
    customer_id: Optional[int]
    first_name: str
    last_name: str
    email: str
    phone: str
    address: str
    city: str
    postal_code: str
    country: str
    items: List[Any]  # JSON field
    payment_method: str
    subtotal: float
    shipping: float
    tax: float
    total: float
    status: str
    notes: Optional[str]
    estimated_delivery: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


# Frontend compatible format
class OrderFrontendResponse(BaseModel):
    id: int
    customerId: Optional[str]
    items: List[OrderItemSchema]
    shippingInfo: ShippingInfoSchema
    paymentMethod: str
    subtotal: float
    discount_amount: float = 0.0
    discount_code: Optional[str] = None
    shipping: float
    tax: float
    total: float
    status: str
    notes: Optional[str]
    createdAt: str
    estimatedDelivery: Optional[str]


class Order(OrderBase):
    id: int
    customer_id: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    estimated_delivery: Optional[datetime] = None 