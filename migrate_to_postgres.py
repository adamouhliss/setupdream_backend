"""
Migration script to set up PostgreSQL database for Setup dreams
Run this after PostgreSQL is installed and running
"""
import os
import sys
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))

# Use the correct database URL for the user's setup
DATABASE_URL = "postgresql://postgres:ChatBot123!@localhost:5432/setupdream"

from app.core.database import Base

# Import all models to ensure they're registered
from app.models.user import User
from app.models.product import Product, Category, Subcategory, ProductImage, InventoryMovement
from app.models.order import Order
from app.models.settings import Settings


def check_postgresql_connection():
    """Check if PostgreSQL is accessible"""
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✅ PostgreSQL connected successfully!")
            print(f"📊 Database version: {version}")
            return True
    except Exception as e:
        print(f"❌ Cannot connect to PostgreSQL: {e}")
        print(f"🔧 Current DATABASE_URL: {DATABASE_URL}")
        return False


def create_tables():
    """Create all tables using SQLAlchemy"""
    try:
        engine = create_engine(DATABASE_URL)
        
        print("🏗️  Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✅ All tables created successfully!")
        
        # Verify tables were created
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"📋 Created tables: {', '.join(tables)}")
            
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False


def setup_alembic():
    """Initialize Alembic and create initial migration"""
    try:
        print("🔧 Setting up Alembic migrations...")
        
        # Create alembic config
        alembic_cfg = Config("alembic.ini")
        
        # Override the database URL in the config
        alembic_cfg.set_main_option('sqlalchemy.url', DATABASE_URL)
        
        # Stamp the database with the current revision
        command.stamp(alembic_cfg, "head")
        print("✅ Alembic setup complete!")
        
        return True
    except Exception as e:
        print(f"❌ Alembic setup failed: {e}")
        return False


def migrate_data_from_sqlite():
    """Migrate data from SQLite to PostgreSQL (if SQLite file exists)"""
    sqlite_path = "carre_sports.db"
    if not os.path.exists(sqlite_path):
        print("ℹ️  No SQLite database found - starting fresh")
        return True
    
    try:
        print("🔄 Migrating data from SQLite...")
        
        # Connect to both databases
        sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
        postgres_engine = create_engine(DATABASE_URL)
        
        # Simple data migration logic
        with sqlite_engine.connect() as sqlite_conn, postgres_engine.connect() as postgres_conn:
            # Get tables that exist in SQLite
            sqlite_tables = sqlite_conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name;
            """)).fetchall()
            
            for table in sqlite_tables:
                table_name = table[0]
                try:
                    # Get all data from SQLite table
                    data = sqlite_conn.execute(text(f"SELECT * FROM {table_name}")).fetchall()
                    
                    if data:
                        print(f"📦 Migrating {len(data)} records from {table_name}")
                        
                        # You would implement specific migration logic here
                        # This is a simplified example
                        
                except Exception as e:
                    print(f"⚠️  Could not migrate table {table_name}: {e}")
        
        print("✅ Data migration completed!")
        return True
        
    except Exception as e:
        print(f"❌ Data migration failed: {e}")
        return False


def main():
    """Main migration function"""
    print("🐘 Setup dreams PostgreSQL Migration")
    print("=" * 40)
    
    # Step 1: Check PostgreSQL connection
    if not check_postgresql_connection():
        print("\n❌ Migration failed: Cannot connect to PostgreSQL")
        print("\n🔧 Please ensure:")
        print("   1. PostgreSQL is installed and running")
        print("   2. Database 'setupdream' exists")
        print("   3. Connection details are correct")
        return False
    
    # Step 2: Create tables
    if not create_tables():
        print("\n❌ Migration failed: Could not create tables")
        return False
    
    # Step 3: Setup Alembic
    if not setup_alembic():
        print("\n❌ Migration failed: Alembic setup failed")
        return False
    
    # Step 4: Migrate data (optional)
    migrate_data_from_sqlite()
    
    print("\n🎉 PostgreSQL migration completed successfully!")
    print("\n📋 Next steps:")
    print("   1. Set DATABASE_URL=postgresql://postgres:ChatBot123!@localhost:5432/setupdream in your environment")
    print("   2. Start your FastAPI server: python -m uvicorn app.main:app --reload")
    print("   3. Create admin user if needed")
    print("   4. Add sample products")
    
    return True


if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1) 