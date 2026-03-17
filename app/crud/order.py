from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..models.order import Order
from ..schemas.order import OrderCreate, OrderUpdate


class CRUDOrder:
    def create(self, db: Session, *, obj_in: OrderCreate) -> Order:
        """Create a new order"""
        # Convert frontend format to database format
        db_obj = Order(
            customer_id=obj_in.customer_id,
            first_name=obj_in.first_name,
            last_name=obj_in.last_name,
            email=obj_in.email,
            phone=obj_in.phone,
            address=obj_in.address,
            city=obj_in.city,
            postal_code=obj_in.postal_code,
            country=obj_in.country,
            items=[item.dict() for item in obj_in.items],
            payment_method=obj_in.payment_method,
            subtotal=obj_in.subtotal,
            discount_amount=obj_in.discount_amount,
            discount_code=obj_in.discount_code,
            shipping=obj_in.shipping,
            tax=obj_in.tax,
            total=obj_in.total,
            status=obj_in.status,
            notes=obj_in.notes,
            estimated_delivery=datetime.now() + timedelta(days=3)
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get(self, db: Session, id: int) -> Optional[Order]:
        """Get order by ID"""
        return db.query(Order).filter(Order.id == id).first()

    def get_multi(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get multiple orders"""
        return db.query(Order).order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

    def get_by_customer(self, db: Session, *, customer_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get orders by customer ID"""
        return db.query(Order).filter(Order.customer_id == customer_id).order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

    def get_by_email(self, db: Session, *, email: str, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get orders by email (for guest orders)"""
        return db.query(Order).filter(Order.email == email).order_by(Order.created_at.desc()).offset(skip).limit(limit).all()

    def update(self, db: Session, *, db_obj: Order, obj_in: OrderUpdate) -> Order:
        """Update an order"""
        if obj_in.status is not None:
            db_obj.status = obj_in.status
        if obj_in.notes is not None:
            db_obj.notes = obj_in.notes
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_by_status(self, db: Session, *, status: str, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get orders by status"""
        return db.query(Order).filter(Order.status == status).order_by(Order.created_at.desc()).offset(skip).limit(limit).all()


order = CRUDOrder() 