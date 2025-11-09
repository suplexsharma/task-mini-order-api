from fastapi import FastAPI, Depends, HTTPException, status, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from typing import List, Optional
from datetime import datetime
import logging

from database import get_db, engine
from models import Base, User, OrderStatus
from schemas import (
    UserRegister, UserLogin, UserResponse, Token, 
    OrderCreate, OrderResponse, RefreshTokenRequest, ErrorResponse
)
from auth import (
    verify_password, create_access_token, create_refresh_token,
    verify_token, get_current_user, get_password_hash
)
from crud import (
    get_user_by_email, create_user, create_order,
    get_user_orders, cancel_order
)
from background_jobs import start_scheduler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
Base.metadata.create_all(bind=engine)

# Hard-code a test user if not exists
def ensure_test_user():
    db = next(get_db())
    test_email = "test@example.com"
    test_user = db.query(User).filter(User.email == test_email).first()
    if not test_user:
        user = User(
            name="Test User",
            email=test_email,
            password_hash=get_password_hash("Password123")
        )
        db.add(user)
        db.commit()
        db.refresh(user)

ensure_test_user()

# Initialize FastAPI app
app = FastAPI(
    title="Mini Order Management API",
    description="Order Management System with JWT Authentication and Background Processing",
    version="1.0.0"
)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Start background scheduler
scheduler = start_scheduler()

# Serve frontend
@app.get("/", response_class=HTMLResponse)
async def serve_frontend():
    with open("frontend.html", "r") as f:
        return f.read()

# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# ==================== AUTHENTICATION ROUTES ====================

@app.post("/auth/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(request: Request, user: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user with name, email, and password.
    Password is hashed using bcrypt before storing.
    """
    try:
        # Check if user already exists
        existing_user = get_user_by_email(db, user.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        try:
            new_user = create_user(db, user)
            logger.info(f"New user registered: {new_user.email}")
            return new_user
        except ValueError as ve:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(ve)
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please ensure password meets requirements."
        )

@app.post("/auth/login", response_model=Token)
@limiter.limit("10/minute")
async def login(request: Request, user: UserLogin, db: Session = Depends(get_db)):
    """
    Login with email and password.
    Returns JWT access token (15 min expiry) and refresh token (7 days expiry).
    """
    try:
        # Verify user credentials
        db_user = get_user_by_email(db, user.email)
        if not db_user or not verify_password(user.password, db_user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Create tokens
        access_token = create_access_token(data={"sub": db_user.email})
        refresh_token = create_refresh_token(data={"sub": db_user.email})
        
        logger.info(f"User logged in: {db_user.email}")
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@app.post("/auth/refresh", response_model=Token)
@limiter.limit("10/minute")
async def refresh_token(request: Request, refresh_request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token.
    """
    try:
        # Verify refresh token
        token_data = verify_token(refresh_request.refresh_token, token_type="refresh")
        
        # Get user
        db_user = get_user_by_email(db, token_data.email)
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        # Create new tokens
        access_token = create_access_token(data={"sub": db_user.email})
        refresh_token = create_refresh_token(data={"sub": db_user.email})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

# ==================== ORDER ROUTES ====================

@app.post("/orders", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_new_order(
    request: Request,
    order: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new order with product name and amount.
    Order starts with 'pending' status.
    """
    try:
        new_order = create_order(db, order, current_user.id)
        logger.info(f"Order created: ID {new_order.id} by user {current_user.email}")
        return new_order
    
    except Exception as e:
        logger.error(f"Order creation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create order"
        )

@app.get("/orders", response_model=List[OrderResponse])
@limiter.limit("30/minute")
async def get_orders(
    request: Request,
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: pending, processing, completed, cancelled"),
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all orders for the logged-in user.
    Optional filters: status, start_date, end_date
    """
    try:
        # Parse dates if provided
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        orders = get_user_orders(db, current_user.id, status_filter, start_dt, end_dt)
        return orders
    
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use YYYY-MM-DD"
        )
    except Exception as e:
        logger.error(f"Get orders error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch orders"
        )

@app.patch("/orders/{order_id}/cancel", response_model=OrderResponse)
@limiter.limit("10/minute")
async def cancel_user_order(
    request: Request,
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel an order if it's still in 'pending' status.
    """
    try:
        cancelled_order = cancel_order(db, order_id, current_user.id)
        
        if not cancelled_order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or cannot be cancelled (not pending)"
            )
        
        logger.info(f"Order cancelled: ID {order_id} by user {current_user.email}")
        return cancelled_order
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel order error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel order"
        )

# ==================== ERROR HANDLERS ====================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Resource not found"}
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

# Shutdown event
@app.on_event("shutdown")
def shutdown_event():
    logger.info("Shutting down scheduler...")
    scheduler.shutdown()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)