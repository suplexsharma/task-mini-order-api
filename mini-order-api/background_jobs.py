import logging
import time
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from database import SessionLocal
from models import OrderStatus
from crud import get_pending_orders, update_order_status


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_pending_orders():
    """
    Background job that processes pending orders.
    Runs every 2-3 minutes and simulates order processing.
    """
    db: Session = SessionLocal()
    try:
        logger.info("Starting background job: Processing pending orders")
        
        # Get all pending orders
        pending_orders = get_pending_orders(db)
        
        if not pending_orders:
            logger.info("No pending orders to process")
            return
        
        logger.info(f"Found {len(pending_orders)} pending orders to process")
        
        for order in pending_orders:
            try:
                # Mark as processing
                logger.info(f"Processing order ID: {order.id} - Product: {order.product_name}")
                update_order_status(db, order, OrderStatus.PROCESSING)
                
                # Simulate processing time (1 second)
                time.sleep(1)
                
                # Mark as completed
                update_order_status(db, order, OrderStatus.COMPLETED)
                logger.info(f"Order ID: {order.id} completed successfully")
                
            except Exception as e:
                logger.error(f"Error processing order ID: {order.id} - Error: {str(e)}")
                db.rollback()
        
        logger.info("Background job completed successfully")
        
    except Exception as e:
        logger.error(f"Background job failed: {str(e)}")
        db.rollback()
    finally:
        db.close()

def start_scheduler():
    """
    Initialize and start the background scheduler.
    Runs the order processing job every 2 minutes.
    """
    scheduler = BackgroundScheduler()
    

    scheduler.add_job(
        process_pending_orders,
        'interval',
        minutes=2,
        id='process_orders',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Background scheduler started - Processing orders every 2 minutes")
    
    return scheduler