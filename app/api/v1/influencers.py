from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from ...api.deps import get_current_active_user, get_db
from ...models.user import User
from ...models.order import Order

router = APIRouter()

@router.get("/dashboard-stats")
def get_influencer_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get aggregated statistics for the influencer's dashboard.
    """
    if not current_user.is_influencer:
        raise HTTPException(status_code=403, detail="Not authorized as an influencer.")
        
    if not current_user.promo_code:
        return {
            "total_revenue": 0,
            "total_commission": 0,
            "total_uses": 0,
            "orders": []
        }

    # Fetch all orders that used this influencer's promo code
    # We filter out "cancelled" status to only count valid sales
    promo_code = current_user.promo_code.upper()
    
    orders = db.query(Order).filter(
        Order.discount_code == promo_code,
        func.lower(Order.status) != "cancelled"
    ).order_by(Order.created_at.desc()).all()

    total_revenue = 0.0
    total_commission = 0.0
    orders_list = []

    for idx, order in enumerate(orders):
        # We assume order.total is the final amount paid by the customer
        revenue = order.total
        # Calculate commission for this specific order based on the user's rate
        commission = revenue * (current_user.commission_rate / 100.0)

        total_revenue += revenue
        total_commission += commission
        
        orders_list.append({
            "id": order.id,
            "total": revenue,
            "commission_earned": commission,
            "status": order.status,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            # We don't expose the customer's full details for privacy
            "customer_name": f"{order.first_name} {order.last_name[0]}." if order.last_name else order.first_name,
            "city": order.city
        })

    return {
        "commission_rate": current_user.commission_rate,
        "customer_discount_rate": current_user.customer_discount_rate,
        "promo_code": current_user.promo_code,
        "total_revenue": round(total_revenue, 2),
        "total_commission": round(total_commission, 2),
        "total_uses": len(orders),
        "recent_orders": orders_list[:50] # Send up to 50 most recent
    }

@router.get("/admin/stats")
def get_all_influencers_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get aggregated statistics for all influencers (Admin only).
    """
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized. Superuser privileges required.")

    # Fetch all influencers
    influencers = db.query(User).filter(User.is_influencer == True).all()
    stats_list = []

    for influencer in influencers:
        total_revenue = 0.0
        total_commission = 0.0
        total_uses = 0

        if influencer.promo_code:
            # Query valid orders for this influencer
            promo_code = influencer.promo_code.upper()
            orders = db.query(Order).filter(
                Order.discount_code == promo_code,
                func.lower(Order.status) != "cancelled"
            ).all()

            total_uses = len(orders)
            for order in orders:
                revenue = order.total
                commission = revenue * (influencer.commission_rate / 100.0)
                total_revenue += revenue
                total_commission += commission

        stats_list.append({
            "id": influencer.id,
            "name": f"{influencer.first_name} {influencer.last_name}" if influencer.first_name else influencer.email,
            "promo_code": influencer.promo_code,
            "commission_rate": influencer.commission_rate,
            "total_uses": total_uses,
            "total_revenue": round(total_revenue, 2),
            "total_commission": round(total_commission, 2)
        })

    # Sort descending by total revenue
    stats_list.sort(key=lambda x: x["total_revenue"], reverse=True)
    return stats_list
