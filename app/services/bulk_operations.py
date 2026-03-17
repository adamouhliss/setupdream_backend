import csv
import io
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from openpyxl import Workbook, load_workbook
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd

from ..crud.product import product_crud, category_crud, subcategory_crud
from ..schemas.product import ProductImportRow, ProductImportResponse, ProductCreate
from ..models.product import Product, Category, Subcategory


class BulkOperationsService:
    
    @staticmethod
    def import_products_from_csv(
        db: Session, 
        csv_content: str,
        user_id: Optional[int] = None
    ) -> ProductImportResponse:
        """Import products from CSV content"""
        
        csv_reader = csv.DictReader(io.StringIO(csv_content))
        total_rows = 0
        success_count = 0
        error_count = 0
        errors = []
        created_products = []
        
        for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 for header
            total_rows += 1
            
            try:
                # Validate and process row
                import_row = BulkOperationsService._process_import_row(db, row)
                
                # Create product
                product_data = BulkOperationsService._convert_import_row_to_product(
                    db, import_row
                )
                
                if product_data:
                    product = product_crud.create(db=db, obj_in=product_data)
                    created_products.append(product.id)
                    success_count += 1
                else:
                    error_count += 1
                    errors.append(f"Row {row_num}: Failed to create product")
                    
            except Exception as e:
                error_count += 1
                errors.append(f"Row {row_num}: {str(e)}")
        
        return ProductImportResponse(
            success_count=success_count,
            error_count=error_count,
            total_rows=total_rows,
            errors=errors,
            created_products=created_products
        )
    
    @staticmethod
    def import_products_from_excel(
        db: Session, 
        excel_content: bytes,
        user_id: Optional[int] = None
    ) -> ProductImportResponse:
        """Import products from Excel file"""
        
        try:
            # Read Excel file
            df = pd.read_excel(io.BytesIO(excel_content))
            
            total_rows = len(df)
            success_count = 0
            error_count = 0
            errors = []
            created_products = []
            
            for index, row in df.iterrows():
                row_num = index + 2  # Account for header
                
                try:
                    # Convert pandas row to dict
                    row_dict = row.to_dict()
                    
                    # Process the row
                    import_row = BulkOperationsService._process_import_row(
                        db, row_dict
                    )
                    
                    # Create product
                    product_data = BulkOperationsService._convert_import_row_to_product(
                        db, import_row
                    )
                    
                    if product_data:
                        product = product_crud.create(db=db, obj_in=product_data)
                        created_products.append(product.id)
                        success_count += 1
                    else:
                        error_count += 1
                        errors.append(f"Row {row_num}: Failed to create product")
                        
                except Exception as e:
                    error_count += 1
                    errors.append(f"Row {row_num}: {str(e)}")
            
            return ProductImportResponse(
                success_count=success_count,
                error_count=error_count,
                total_rows=total_rows,
                errors=errors,
                created_products=created_products
            )
            
        except Exception as e:
            return ProductImportResponse(
                success_count=0,
                error_count=0,
                total_rows=0,
                errors=[f"Failed to read Excel file: {str(e)}"],
                created_products=[]
            )
    
    @staticmethod
    def _process_import_row(db: Session, row: Dict[str, Any]) -> ProductImportRow:
        """Process and validate an import row"""
        
        # Clean and validate required fields
        required_fields = ['name', 'price', 'sku', 'category_name']
        for field in required_fields:
            if not row.get(field):
                raise ValueError(f"Missing required field: {field}")
        
        # Convert numeric fields
        try:
            price = float(row['price'])
            if price <= 0:
                raise ValueError("Price must be greater than 0")
        except (ValueError, TypeError):
            raise ValueError("Invalid price format")
        
        # Handle optional numeric fields
        sale_price = None
        if row.get('sale_price'):
            try:
                sale_price = float(row['sale_price'])
                if sale_price <= 0:
                    raise ValueError("Sale price must be greater than 0")
            except (ValueError, TypeError):
                raise ValueError("Invalid sale price format")
        
        stock_quantity = 0
        if row.get('stock_quantity'):
            try:
                stock_quantity = int(row['stock_quantity'])
                if stock_quantity < 0:
                    raise ValueError("Stock quantity cannot be negative")
            except (ValueError, TypeError):
                raise ValueError("Invalid stock quantity format")
        
        low_stock_threshold = 10
        if row.get('low_stock_threshold'):
            try:
                low_stock_threshold = int(row['low_stock_threshold'])
                if low_stock_threshold < 0:
                    raise ValueError("Low stock threshold cannot be negative")
            except (ValueError, TypeError):
                raise ValueError("Invalid low stock threshold format")
        
        reorder_level = 5
        if row.get('reorder_level'):
            try:
                reorder_level = int(row['reorder_level'])
                if reorder_level < 0:
                    raise ValueError("Reorder level cannot be negative")
            except (ValueError, TypeError):
                raise ValueError("Invalid reorder level format")
        
        cost_price = None
        if row.get('cost_price'):
            try:
                cost_price = float(row['cost_price'])
                if cost_price <= 0:
                    raise ValueError("Cost price must be greater than 0")
            except (ValueError, TypeError):
                raise ValueError("Invalid cost price format")
        
        weight = None
        if row.get('weight'):
            try:
                weight = float(row['weight'])
                if weight <= 0:
                    raise ValueError("Weight must be greater than 0")
            except (ValueError, TypeError):
                raise ValueError("Invalid weight format")
        
        # Handle boolean fields
        is_active = True
        if row.get('is_active'):
            is_active = str(row['is_active']).lower() in ['true', '1', 'yes', 'y']
        
        is_featured = False
        if row.get('is_featured'):
            is_featured = str(row['is_featured']).lower() in ['true', '1', 'yes', 'y']
        
        return ProductImportRow(
            name=str(row['name']).strip(),
            description=str(row.get('description', '')).strip() or None,
            price=price,
            sale_price=sale_price,
            sku=str(row['sku']).strip(),
            stock_quantity=stock_quantity,
            low_stock_threshold=low_stock_threshold,
            reorder_level=reorder_level,
            category_name=str(row['category_name']).strip(),
            subcategory_name=str(row.get('subcategory_name', '')).strip() or None,
            brand=str(row.get('brand', '')).strip() or None,
            size=str(row.get('size', '')).strip() or None,
            color=str(row.get('color', '')).strip() or None,
            material=str(row.get('material', '')).strip() or None,
            weight=weight,
            dimensions=str(row.get('dimensions', '')).strip() or None,
            cost_price=cost_price,
            is_active=is_active,
            is_featured=is_featured
        )
    
    @staticmethod
    def _convert_import_row_to_product(
        db: Session, 
        import_row: ProductImportRow
    ) -> Optional[ProductCreate]:
        """Convert import row to ProductCreate schema"""
        
        # Get or create category
        category = category_crud.get_by_name(db=db, name=import_row.category_name)
        if not category:
            # Create new category
            from ..schemas.product import CategoryCreate
            category_data = CategoryCreate(name=import_row.category_name)
            category = category_crud.create(db=db, obj_in=category_data)
        
        # Get or create subcategory if specified
        subcategory_id = None
        if import_row.subcategory_name:
            subcategory = subcategory_crud.get_by_name_and_category(
                db=db, 
                name=import_row.subcategory_name, 
                category_id=category.id
            )
            if not subcategory:
                # Create new subcategory
                from ..schemas.product import SubcategoryCreate
                subcategory_data = SubcategoryCreate(
                    name=import_row.subcategory_name,
                    category_id=category.id
                )
                subcategory = subcategory_crud.create(db=db, obj_in=subcategory_data)
            subcategory_id = subcategory.id
        
        # Check if SKU already exists
        existing_product = product_crud.get_by_sku(db=db, sku=import_row.sku)
        if existing_product:
            raise ValueError(f"Product with SKU '{import_row.sku}' already exists")
        
        return ProductCreate(
            name=import_row.name,
            description=import_row.description,
            price=import_row.price,
            sale_price=import_row.sale_price,
            sku=import_row.sku,
            stock_quantity=import_row.stock_quantity,
            low_stock_threshold=import_row.low_stock_threshold,
            reorder_level=import_row.reorder_level,
            category_id=category.id,
            subcategory_id=subcategory_id,
            brand=import_row.brand,
            size=import_row.size,
            color=import_row.color,
            material=import_row.material,
            weight=import_row.weight,
            dimensions=import_row.dimensions,
            cost_price=import_row.cost_price,
            is_active=import_row.is_active,
            is_featured=import_row.is_featured
        )
    
    @staticmethod
    def export_products_to_csv(
        db: Session,
        include_inactive: bool = False,
        category_ids: Optional[List[int]] = None
    ) -> str:
        """Export products to CSV format"""
        
        # Get products
        products = product_crud.get_multi(
            db=db,
            limit=10000,  # Large limit for export
            is_active=None if include_inactive else True,
            category_id=category_ids[0] if category_ids and len(category_ids) == 1 else None
        )
        
        # Filter by multiple categories if specified
        if category_ids and len(category_ids) > 1:
            products = [p for p in products if p.category_id in category_ids]
        
        # Prepare CSV data
        csv_data = io.StringIO()
        fieldnames = [
            'id', 'name', 'description', 'price', 'sale_price', 'sku',
            'stock_quantity', 'low_stock_threshold', 'reorder_level',
            'category_name', 'subcategory_name', 'brand', 'size', 'color',
            'material', 'weight', 'dimensions', 'cost_price', 'is_active',
            'is_featured', 'view_count', 'sales_count', 'created_at'
        ]
        
        writer = csv.DictWriter(csv_data, fieldnames=fieldnames)
        writer.writeheader()
        
        for product in products:
            writer.writerow({
                'id': product.id,
                'name': product.name,
                'description': product.description,
                'price': product.price,
                'sale_price': product.sale_price,
                'sku': product.sku,
                'stock_quantity': product.stock_quantity,
                'low_stock_threshold': product.low_stock_threshold,
                'reorder_level': product.reorder_level,
                'category_name': product.category.name if product.category else '',
                'subcategory_name': product.subcategory.name if product.subcategory else '',
                'brand': product.brand,
                'size': product.size,
                'color': product.color,
                'material': product.material,
                'weight': product.weight,
                'dimensions': product.dimensions,
                'cost_price': product.cost_price,
                'is_active': product.is_active,
                'is_featured': product.is_featured,
                'view_count': product.view_count,
                'sales_count': product.sales_count,
                'created_at': product.created_at.isoformat() if product.created_at else ''
            })
        
        return csv_data.getvalue()
    
    @staticmethod
    def export_products_to_excel(
        db: Session,
        include_inactive: bool = False,
        category_ids: Optional[List[int]] = None
    ) -> bytes:
        """Export products to Excel format"""
        
        # Get products
        products = product_crud.get_multi(
            db=db,
            limit=10000,  # Large limit for export
            is_active=None if include_inactive else True,
            category_id=category_ids[0] if category_ids and len(category_ids) == 1 else None
        )
        
        # Filter by multiple categories if specified
        if category_ids and len(category_ids) > 1:
            products = [p for p in products if p.category_id in category_ids]
        
        # Prepare data for Excel
        data = []
        for product in products:
            data.append({
                'ID': product.id,
                'Name': product.name,
                'Description': product.description,
                'Price': product.price,
                'Sale Price': product.sale_price,
                'SKU': product.sku,
                'Stock Quantity': product.stock_quantity,
                'Low Stock Threshold': product.low_stock_threshold,
                'Reorder Level': product.reorder_level,
                'Category': product.category.name if product.category else '',
                'Subcategory': product.subcategory.name if product.subcategory else '',
                'Brand': product.brand,
                'Size': product.size,
                'Color': product.color,
                'Material': product.material,
                'Weight': product.weight,
                'Dimensions': product.dimensions,
                'Cost Price': product.cost_price,
                'Active': product.is_active,
                'Featured': product.is_featured,
                'View Count': product.view_count,
                'Sales Count': product.sales_count,
                'Created At': product.created_at.isoformat() if product.created_at else ''
            })
        
        # Create Excel workbook
        df = pd.DataFrame(data)
        excel_buffer = io.BytesIO()
        
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Products', index=False)
            
            # Auto-adjust column widths
            worksheet = writer.sheets['Products']
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        excel_buffer.seek(0)
        return excel_buffer.getvalue()
    
    @staticmethod
    def get_import_template() -> str:
        """Generate CSV template for product import"""
        
        template_data = io.StringIO()
        fieldnames = [
            'name', 'description', 'price', 'sale_price', 'sku',
            'stock_quantity', 'low_stock_threshold', 'reorder_level',
            'category_name', 'subcategory_name', 'brand', 'size', 'color',
            'material', 'weight', 'dimensions', 'cost_price', 'is_active',
            'is_featured'
        ]
        
        writer = csv.DictWriter(template_data, fieldnames=fieldnames)
        writer.writeheader()
        
        # Add sample row
        writer.writerow({
            'name': 'Sample Product',
            'description': 'This is a sample product description',
            'price': '99.99',
            'sale_price': '79.99',
            'sku': 'SAMPLE-001',
            'stock_quantity': '50',
            'low_stock_threshold': '10',
            'reorder_level': '5',
            'category_name': 'Equipment',
            'subcategory_name': 'Tennis',
            'brand': 'Sample Brand',
            'size': 'Medium',
            'color': 'Blue',
            'material': 'Plastic',
            'weight': '0.5',
            'dimensions': '20x15x10 cm',
            'cost_price': '40.00',
            'is_active': 'true',
            'is_featured': 'false'
        })
        
        return template_data.getvalue()


# Create service instance
bulk_operations_service = BulkOperationsService() 