from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Optional
from datetime import datetime

from models import User, Order, OrderStatus
from schemas import UserRegister, OrderCreate
from auth import get_password_hash


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserRegister):
    db_user = User(
        name=user.name,
        email=user.email,
        password_hash=get_password_hash(user.password)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def create_order(db: Session, order: OrderCreate, user_id: int) -> Order:
    db_order = Order(
        user_id=user_id,
        product_name=order.product_name,
        amount=order.amount,
        status=OrderStatus.PENDING
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order

def get_user_orders(
    db: Session, 
    user_id: int, 
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> List[Order]:
    query = db.query(Order).filter(Order.user_id == user_id)
    
    if status:
        query = query.filter(Order.status == status)
    
    if start_date:
        query = query.filter(Order.created_at >= start_date)
    
    if end_date:
        query = query.filter(Order.created_at <= end_date)
    
    return query.order_by(Order.created_at.desc()).all()

def get_order_by_id(db: Session, order_id: int, user_id: int) -> Optional[Order]:
    return db.query(Order).filter(
        and_(Order.id == order_id, Order.user_id == user_id)
    ).first()

def cancel_order(db: Session, order_id: int, user_id: int) -> Optional[Order]:
    order = get_order_by_id(db, order_id, user_id)
    if order and order.status == OrderStatus.PENDING:
        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(order)
        return order
    return None

def get_pending_orders(db: Session) -> List[Order]:
    return db.query(Order).filter(Order.status == OrderStatus.PENDING).all()

def update_order_status(db: Session, order: Order, status: OrderStatus) -> Order:
    order.status = status
    order.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(order)
    return order