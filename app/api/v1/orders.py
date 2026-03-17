from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import logging

from ...api.deps import get_db, get_current_active_user, get_current_active_superuser, get_current_user_or_none
from ...crud import order as order_crud
from ...crud.product import product_crud  # Add product_crud import for inventory management
from ...models.user import User
from ...schemas.order import OrderCreate, OrderUpdate, OrderResponse, OrderFrontendResponse, ShippingInfoSchema, OrderItemSchema
from ...services.whatsapp_service import whatsapp_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/validate-promo")
def validate_promo_code(code: str = Query(...), db: Session = Depends(get_db)):
    """Validate a promo code and return the discount percentage."""
    normalized_code = code.strip().upper()
    
    # Check if this matches an influencer promo code
    influencer = db.query(User).filter(
        User.promo_code == normalized_code,
        User.is_influencer == True,
        User.is_active == True
    ).first()
    
    if not influencer:
        raise HTTPException(status_code=404, detail="Invalid or expired promo code.")
        
    return {
        "valid": True,
        "discount_rate": influencer.customer_discount_rate,
        "code": normalized_code
    }


@router.post("/", response_model=OrderResponse)
def create_order(
    *,
    db: Session = Depends(get_db),
    order_in: OrderCreate,
    current_user: Optional[User] = Depends(get_current_user_or_none)
):
    """Create a new order"""
    # If user is authenticated, link the order to them
    if current_user:
        order_in.customer_id = current_user.id
    
    order = order_crud.create(db=db, obj_in=order_in)
    
    # Send WhatsApp notification to admin (non-blocking)
    try:
        order_data = {
            "id": order.id,
            "first_name": order.first_name,
            "last_name": order.last_name,
            "phone": order.phone,
            "city": order.city,
            "items": order.items,  # This is already a JSON field
            "total": order.total,
            "payment_method": order.payment_method,
            "created_at": order.created_at.isoformat() if order.created_at else None
        }
        
        # Send notification asynchronously (don't block order creation)
        import threading
        def send_notification():
            try:
                whatsapp_service.send_order_notification(order_data)
            except Exception as e:
                logger.error(f"WhatsApp notification failed for order {order.id}: {e}")
        
        # Start notification in background thread
        notification_thread = threading.Thread(target=send_notification)
        notification_thread.daemon = True
        notification_thread.start()
        
        logger.info(f"Order {order.id} created, WhatsApp notification queued")
        
    except Exception as e:
        # Log error but don't fail order creation
        logger.error(f"Error queuing WhatsApp notification for order {order.id}: {e}")
    
    return order


@router.get("/", response_model=List[OrderFrontendResponse])
def get_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[str] = Query(None)
):
    """Get all orders (admin only)"""
    if status:
        orders = order_crud.get_by_status(db=db, status=status, skip=skip, limit=limit)
    else:
        orders = order_crud.get_multi(db=db, skip=skip, limit=limit)
    
    # Convert to frontend format
    return [convert_to_frontend_format(order) for order in orders]


@router.get("/my-orders", response_model=List[OrderFrontendResponse])
def get_my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100)
):
    """Get current user's orders"""
    orders = order_crud.get_by_customer(db=db, customer_id=current_user.id, skip=skip, limit=limit)
    return [convert_to_frontend_format(order) for order in orders]


def convert_to_frontend_format(order) -> OrderFrontendResponse:
    """Convert database order to frontend format"""
    shipping_info = ShippingInfoSchema(
        firstName=order.first_name,
        lastName=order.last_name,
        email=order.email,
        phone=order.phone,
        address=order.address,
        city=order.city,
        postalCode=order.postal_code,
        country=order.country
    )
    
    return OrderFrontendResponse(
        id=order.id,
        customerId=str(order.customer_id) if order.customer_id else "guest",
        items=order.items,
        shippingInfo=shipping_info,
        paymentMethod=order.payment_method,
        subtotal=order.subtotal,
        discount_amount=order.discount_amount,
        discount_code=order.discount_code,
        shipping=order.shipping,
        tax=order.tax,
        total=order.total,
        status=order.status,
        notes=order.notes,
        createdAt=order.created_at.isoformat(),
        estimatedDelivery=order.estimated_delivery.isoformat() if order.estimated_delivery else None
    )


@router.put("/{order_id}", response_model=OrderFrontendResponse)
def update_order(
    order_id: int,
    order_update: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_superuser)
):
    """Update an order (admin only)"""
    order = order_crud.get(db=db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Store the old status before updating
    old_status = order.status
    
    # Update the order
    order = order_crud.update(db=db, db_obj=order, obj_in=order_update)
    
    # Handle inventory management when status changes
    new_status = order.status
    
    # Define statuses that should trigger inventory decrement
    inventory_impacting_statuses = {"paid"}  # Only paid orders impact inventory
    non_inventory_statuses = {"pending", "confirmed", "shipped", "returned", "cancelled"}
    
    # If status changed from non-inventory to inventory-impacting, decrement stock
    if (old_status in non_inventory_statuses and 
        new_status in inventory_impacting_statuses):
        
        try:
            # Process each item in the order to decrement stock
            for item in order.items:
                product_id = item.get("productId")
                quantity = item.get("quantity", 0)
                
                if product_id and quantity > 0:
                    # Decrement stock using the existing inventory management system
                    product_crud.update_stock(
                        db=db,
                        product_id=product_id,
                        quantity_change=-quantity,  # Negative to decrease stock
                        movement_type="out",
                        reason="order_fulfillment",
                        reference_id=f"order_{order.id}",
                        user_id=current_user.id
                    )
        except Exception as e:
            # If inventory update fails, rollback and raise error
            db.rollback()
            raise HTTPException(
                status_code=400, 
                detail=f"Failed to update inventory: {str(e)}"
            )
    
    return convert_to_frontend_format(order)


@router.get("/{order_id}", response_model=OrderFrontendResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get order by ID"""
    order = order_crud.get(db=db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Check if user has permission to view this order
    if not current_user.is_superuser and order.customer_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not enough permissions")
    
    return convert_to_frontend_format(order)


# Test endpoint for WhatsApp service
@router.get("/test/whatsapp-status")
def test_whatsapp_status(
    current_user: User = Depends(get_current_active_superuser)
):
    """Test WhatsApp service status (admin only)"""
    return whatsapp_service.test_connection() 