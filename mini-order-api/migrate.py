from database import engine, Base
from models import User, Order
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """
    Create all database tables based on SQLAlchemy models.
    This will create tables with all columns, indexes, and relationships defined in models.py
    """
    try:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info(" Database tables created successfully!")
        
        logger.info("\n Tables created:")
        logger.info("   users:")
        logger.info("     - id (INTEGER PRIMARY KEY)")
        logger.info("     - name (TEXT)")
        logger.info("     - email (TEXT UNIQUE, INDEXED)")
        logger.info("     - password_hash (TEXT)")
        logger.info("     - created_at (TIMESTAMP)")
        
        logger.info("\n   orders:")
        logger.info("     - id (INTEGER PRIMARY KEY)")
        logger.info("     - user_id (INTEGER, FOREIGN KEY → users.id, INDEXED)")
        logger.info("     - product_name (TEXT)")
        logger.info("     - amount (REAL)")
        logger.info("     - status (TEXT, INDEXED)")
        logger.info("     - created_at (TIMESTAMP, INDEXED)")
        logger.info("     - updated_at (TIMESTAMP)")
        
        logger.info("\n🔗 Relationships:")
        logger.info("   - orders.user_id → users.id (CASCADE DELETE)")
        
        logger.info("\n Indexes created:")
        logger.info("   - idx_users_email")
        logger.info("   - idx_orders_user_id")
        logger.info("   - idx_orders_status")
        logger.info("   - idx_orders_created_at")
        
        logger.info("\n Database ready! Run 'python main.py' to start the server.")
        
    except Exception as e:
        logger.error(f" Error creating tables: {str(e)}")
        raise

if __name__ == "__main__":
    create_tables()