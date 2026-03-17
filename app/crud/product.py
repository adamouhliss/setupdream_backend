from typing import Any, Dict, List, Optional, Union
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, text

from ..models.product import Product, Category, ProductImage, Subcategory, InventoryMovement
from ..models.product_variant import ProductVariant
from ..schemas.product import ProductCreate, ProductUpdate, CategoryCreate, CategoryUpdate, SubcategoryCreate, SubcategoryUpdate, InventoryMovementCreate


class CRUDProduct:
    def get(self, db: Session, id: Any) -> Optional[Product]:
        return db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.subcategory),
            joinedload(Product.images),
            joinedload(Product.variants)
        ).filter(Product.id == id).first()

    def get_by_sku(self, db: Session, *, sku: str) -> Optional[Product]:
        return db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.subcategory),
            joinedload(Product.images),
            joinedload(Product.variants)
        ).filter(Product.sku == sku).first()

    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        category_id: Optional[int] = None,
        subcategory_id: Optional[int] = None,
        is_active: Optional[bool] = True,
        is_featured: Optional[bool] = None,
        search: Optional[str] = None,
        low_stock_only: bool = False,
        needs_reorder_only: bool = False
    ) -> List[Product]:
        query = db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.subcategory),
            joinedload(Product.images),
            joinedload(Product.variants)
        )
        
        if is_active is not None:
            query = query.filter(Product.is_active == is_active)
        
        if is_featured is not None:
            query = query.filter(Product.is_featured == is_featured)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
            
        if subcategory_id:
            query = query.filter(Product.subcategory_id == subcategory_id)
        
        if search:
            search_filter = or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
                Product.brand.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
            
        if low_stock_only:
            query = query.filter(Product.stock_quantity <= Product.low_stock_threshold)
            
        if needs_reorder_only:
            query = query.filter(Product.stock_quantity <= Product.reorder_level)
        
        return query.offset(skip).limit(limit).all()

    def get_count(
        self,
        db: Session,
        *,
        category_id: Optional[int] = None,
        subcategory_id: Optional[int] = None,
        is_active: Optional[bool] = True,
        is_featured: Optional[bool] = None,
        search: Optional[str] = None,
        low_stock_only: bool = False,
        needs_reorder_only: bool = False
    ) -> int:
        query = db.query(func.count(Product.id))
        
        if is_active is not None:
            query = query.filter(Product.is_active == is_active)
        
        if is_featured is not None:
            query = query.filter(Product.is_featured == is_featured)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
            
        if subcategory_id:
            query = query.filter(Product.subcategory_id == subcategory_id)
        
        if search:
            search_filter = or_(
                Product.name.ilike(f"%{search}%"),
                Product.description.ilike(f"%{search}%"),
                Product.brand.ilike(f"%{search}%"),
                Product.sku.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
            
        if low_stock_only:
            query = query.filter(Product.stock_quantity <= Product.low_stock_threshold)
            
        if needs_reorder_only:
            query = query.filter(Product.stock_quantity <= Product.reorder_level)
        
        return query.scalar()

    def create(self, db: Session, *, obj_in: ProductCreate) -> Product:
        obj_data = obj_in.model_dump()
        variants_data = obj_data.pop("variants", [])
        
        db_obj = Product(**obj_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        
        # Create variants if provided
        if variants_data:
            for variant in variants_data:
                db_variant = ProductVariant(
                    product_id=db_obj.id,
                    **variant.model_dump()
                )
                db.add(db_variant)
            db.commit()
            db.refresh(db_obj)
            
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: Product,
        obj_in: Union[ProductUpdate, Dict[str, Any]]
    ) -> Product:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
            
        # Handle variants update
        if "variants" in update_data:
            variants_data = update_data.pop("variants")
            
            # Remove existing variants (simple replacement strategy)
            db.query(ProductVariant).filter(ProductVariant.product_id == db_obj.id).delete()
            
            # Create new variants
            if variants_data:
                for variant in variants_data:
                    variant_data = variant if isinstance(variant, dict) else variant.model_dump()
                    db_variant = ProductVariant(
                        product_id=db_obj.id,
                        **variant_data
                    )
                    db.add(db_variant)
        
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Product:
        obj = db.query(Product).get(id)
        db.delete(obj)
        db.commit()
        return obj

    def get_featured(self, db: Session, *, limit: int = 10) -> List[Product]:
        return db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.subcategory),
            joinedload(Product.images),
            joinedload(Product.variants)
        ).filter(
            and_(Product.is_featured == True, Product.is_active == True)
        ).limit(limit).all()

    # New inventory management methods
    def get_low_stock_products(self, db: Session, *, limit: int = 100) -> List[Product]:
        """Get products with low stock"""
        return db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.subcategory)
        ).filter(
            and_(
                Product.is_active == True,
                Product.stock_quantity <= Product.low_stock_threshold
            )
        ).limit(limit).all()

    def get_reorder_products(self, db: Session, *, limit: int = 100) -> List[Product]:
        """Get products that need reordering"""
        return db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.subcategory)
        ).filter(
            and_(
                Product.is_active == True,
                Product.stock_quantity <= Product.reorder_level
            )
        ).limit(limit).all()

    def get_out_of_stock_products(self, db: Session, *, limit: int = 100) -> List[Product]:
        """Get products that are out of stock"""
        return db.query(Product).options(
            joinedload(Product.category),
            joinedload(Product.subcategory)
        ).filter(
            and_(
                Product.is_active == True,
                Product.stock_quantity == 0
            )
        ).limit(limit).all()

    def update_stock(
        self, 
        db: Session, 
        *, 
        product_id: int, 
        quantity_change: int, 
        movement_type: str,
        reason: str = None,
        reference_id: str = None,
        user_id: int = None
    ) -> Product:
        """Update product stock and record inventory movement"""
        # Get product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError(f"Product {product_id} not found")
        
        # Update stock
        old_quantity = product.stock_quantity
        new_quantity = max(0, old_quantity + quantity_change)
        product.stock_quantity = new_quantity
        
        # Record inventory movement
        movement = InventoryMovement(
            product_id=product_id,
            movement_type=movement_type,
            quantity=quantity_change,
            reason=reason,
            reference_id=reference_id,
            created_by=user_id
        )
        
        db.add(product)
        db.add(movement)
        db.commit()
        db.refresh(product)
        
        return product

    def get_inventory_summary(self, db: Session) -> Dict[str, Any]:
        """Get inventory summary statistics"""
        total_products = db.query(func.count(Product.id)).filter(Product.is_active == True).scalar()
        
        low_stock_count = db.query(func.count(Product.id)).filter(
            and_(
                Product.is_active == True,
                Product.stock_quantity <= Product.low_stock_threshold
            )
        ).scalar()
        
        reorder_count = db.query(func.count(Product.id)).filter(
            and_(
                Product.is_active == True,
                Product.stock_quantity <= Product.reorder_level
            )
        ).scalar()
        
        out_of_stock_count = db.query(func.count(Product.id)).filter(
            and_(
                Product.is_active == True,
                Product.stock_quantity == 0
            )
        ).scalar()
        
        total_stock_value = db.query(
            func.sum(Product.price * Product.stock_quantity)
        ).filter(Product.is_active == True).scalar() or 0
        
        return {
            "total_products": total_products,
            "low_stock_count": low_stock_count,
            "reorder_count": reorder_count,
            "out_of_stock_count": out_of_stock_count,
            "total_stock_value": float(total_stock_value)
        }


class CRUDCategory:
    def get(self, db: Session, id: Any) -> Optional[Category]:
        return db.query(Category).options(
            joinedload(Category.subcategories)
        ).filter(Category.id == id).first()

    def get_by_name(self, db: Session, *, name: str) -> Optional[Category]:
        return db.query(Category).filter(Category.name == name).first()

    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        is_active: bool = True
    ) -> List[Category]:
        query = db.query(Category).options(joinedload(Category.subcategories))
        if is_active:
            query = query.filter(Category.is_active == True)
        return query.order_by(Category.sort_order, Category.name).offset(skip).limit(limit).all()

    def get_count(self, db: Session, *, is_active: bool = True) -> int:
        query = db.query(func.count(Category.id))
        if is_active:
            query = query.filter(Category.is_active == True)
        return query.scalar()

    def create(self, db: Session, *, obj_in: CategoryCreate) -> Category:
        db_obj = Category(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: Category,
        obj_in: Union[CategoryUpdate, Dict[str, Any]]
    ) -> Category:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Category:
        obj = db.query(Category).get(id)
        db.delete(obj)
        db.commit()
        return obj


class CRUDSubcategory:
    def get(self, db: Session, id: Any) -> Optional[Subcategory]:
        return db.query(Subcategory).options(
            joinedload(Subcategory.category)
        ).filter(Subcategory.id == id).first()

    def get_by_name_and_category(self, db: Session, *, name: str, category_id: int) -> Optional[Subcategory]:
        return db.query(Subcategory).filter(
            and_(Subcategory.name == name, Subcategory.category_id == category_id)
        ).first()

    def get_by_category(
        self, 
        db: Session, 
        *, 
        category_id: int,
        is_active: bool = True
    ) -> List[Subcategory]:
        query = db.query(Subcategory).filter(Subcategory.category_id == category_id)
        if is_active:
            query = query.filter(Subcategory.is_active == True)
        return query.order_by(Subcategory.sort_order, Subcategory.name).all()

    def get_all(
        self, 
        db: Session, 
        *, 
        is_active: Optional[bool] = None,
        category_id: Optional[int] = None
    ) -> List[Subcategory]:
        """Get all subcategories with optional filtering"""
        query = db.query(Subcategory).options(joinedload(Subcategory.category))
        
        if is_active is not None:
            query = query.filter(Subcategory.is_active == is_active)
        if category_id is not None:
            query = query.filter(Subcategory.category_id == category_id)
            
        return query.order_by(Subcategory.sort_order, Subcategory.name).all()

    def get_multi(
        self, 
        db: Session, 
        *, 
        skip: int = 0, 
        limit: int = 100,
        category_id: Optional[int] = None,
        is_active: bool = True
    ) -> List[Subcategory]:
        query = db.query(Subcategory).options(joinedload(Subcategory.category))
        
        if category_id:
            query = query.filter(Subcategory.category_id == category_id)
        if is_active:
            query = query.filter(Subcategory.is_active == True)
            
        return query.order_by(Subcategory.sort_order, Subcategory.name).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: SubcategoryCreate) -> Subcategory:
        db_obj = Subcategory(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: Subcategory,
        obj_in: Union[SubcategoryUpdate, Dict[str, Any]]
    ) -> Subcategory:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)
        
        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])
        
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: int) -> Subcategory:
        obj = db.query(Subcategory).get(id)
        db.delete(obj)
        db.commit()
        return obj


class CRUDInventoryMovement:
    def get_by_product(
        self, 
        db: Session, 
        *, 
        product_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[InventoryMovement]:
        return db.query(InventoryMovement).filter(
            InventoryMovement.product_id == product_id
        ).order_by(InventoryMovement.created_at.desc()).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: InventoryMovementCreate) -> InventoryMovement:
        db_obj = InventoryMovement(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_recent_movements(
        self, 
        db: Session, 
        *, 
        limit: int = 50
    ) -> List[InventoryMovement]:
        return db.query(InventoryMovement).order_by(
            InventoryMovement.created_at.desc()
        ).limit(limit).all()


# Create instances
product_crud = CRUDProduct()
category_crud = CRUDCategory()
subcategory_crud = CRUDSubcategory()
inventory_movement_crud = CRUDInventoryMovement() 