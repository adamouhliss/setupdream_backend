
from app.core.database import SessionLocal
from app.models.product import Product
import os

db = SessionLocal()
try:
    products = db.query(Product).limit(10).all()
    print(f"Checking {len(products)} products:")
    for p in products:
        print(f"Product ID: {p.id}, Name: {p.name}, Image URL: {p.image_url}")
        if p.image_url:
            # Check if file exists locally
            path = p.image_url.lstrip('/')
            exists = os.path.exists(path)
            print(f"  File path: {path}, Exists: {exists}")
finally:
    db.close()
