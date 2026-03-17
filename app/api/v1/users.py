from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from math import ceil

from ...api.deps import get_current_active_superuser, get_current_active_user, get_db
from ...crud.user import user
from ...models.user import User
from ...schemas.user import User as UserSchema, UserCreate, UserUpdate, UserResponse

router = APIRouter()


@router.get("/")
def read_users(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Retrieve users with pagination (admin only).
    """
    # Check if user is superuser
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=400, detail="The user doesn't have enough privileges"
        )
    
    try:
        users = user.get_multi(db, skip=skip, limit=limit)
        total_users = db.query(User).count()
        
        # Convert to simple dictionaries to avoid serialization issues
        user_list = []
        for u in users:
            user_dict = {
                "id": u.id,
                "email": u.email,
                "first_name": u.first_name,
                "last_name": u.last_name,
                "phone": u.phone,
                "is_active": u.is_active,
                "is_superuser": u.is_superuser,
                "is_verified": getattr(u, 'is_verified', False),
                "is_influencer": getattr(u, 'is_influencer', False),
                "promo_code": getattr(u, 'promo_code', None),
                "commission_rate": getattr(u, 'commission_rate', None),
                "customer_discount_rate": getattr(u, 'customer_discount_rate', None),
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "total_orders": 0,
                "total_spent": 0,
            }
            user_list.append(user_dict)
        
        return {
            "items": user_list,
            "total": total_users,
            "page": (skip // limit) + 1,
            "per_page": limit,
            "pages": ceil(total_users / limit) if limit > 0 else 1
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")


@router.post("/", response_model=UserResponse)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Create new user (admin only).
    """
    user_obj = user.get_by_email(db, email=user_in.email)
    if user_obj:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    try:
        user_obj = user.create(db, obj_in=user_in)
        return user_obj
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error creating user: {str(e)}")


@router.get("/me", response_model=UserResponse)
def read_user_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user.
    """
    return current_user


@router.put("/me", response_model=UserResponse)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update own user.
    """
    user_obj = user.update(db, db_obj=current_user, obj_in=user_in)
    return user_obj


@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Update a user (admin only).
    """
    user_obj = user.get(db, id=user_id)
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")
    user_obj = user.update(db, db_obj=user_obj, obj_in=user_in)
    return user_obj


@router.put("/{user_id}/influencer", response_model=UserResponse)
def update_user_influencer_status(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Update a user's influencer status and promo settings (admin only).
    """
    user_obj = user.get(db, id=user_id)
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Check if a promo code is being set, and ensure it's unique
    if user_in.promo_code and user_in.promo_code != getattr(user_obj, 'promo_code', None):
        existing_promo = db.query(User).filter(User.promo_code == user_in.promo_code.upper()).first()
        if existing_promo:
            raise HTTPException(status_code=400, detail="This promo code is already in use by another influencer.")
            
    # Normalize promo code to uppercase
    update_data = user_in.model_dump(exclude_unset=True)
    if 'promo_code' in update_data and update_data['promo_code']:
        update_data['promo_code'] = update_data['promo_code'].upper()
        
    user_obj = user.update(db, db_obj=user_obj, obj_in=update_data)
    return user_obj


@router.get("/{user_id}", response_model=UserResponse)
def read_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Get user by ID (admin only).
    """
    user_obj = user.get(db, id=user_id)
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")
    return user_obj


@router.delete("/{user_id}", response_model=UserResponse)
def delete_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Delete user (admin only).
    """
    user_obj = user.get(db, id=user_id)
    if not user_obj:
        raise HTTPException(status_code=404, detail="User not found")
    if user_obj.id == current_user.id:
        raise HTTPException(status_code=400, detail="Users cannot delete themselves")
    user_obj = user.remove(db, id=user_id)
    return user_obj 