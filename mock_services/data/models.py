from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()

class CustomerDB(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    mobile_number = Column(String, unique=True, index=True)
    name = Column(String)
    has_subscription = Column(Boolean, default=False)
    subscription_expiry = Column(DateTime, nullable=True)
    mock_otp = Column(String, default="1234")
    wallet_balance = Column(Float, default=0.0)
    
    orders = relationship("OrderDB", back_populates="customer")

class OrderDB(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True, index=True)
    mobile_number = Column(String, ForeignKey("customers.mobile_number"))
    restaurant = Column(String)
    status = Column(String) # Preparing, Out for Delivery, Delivered, Delayed, Cancelled
    delay_reason = Column(String, nullable=True)
    address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    refund_status = Column(String, nullable=True)
    driver_eta = Column(String, nullable=True)
    driver_location = Column(String, nullable=True)
    driver_instruction = Column(String, nullable=True)
    
    customer = relationship("CustomerDB", back_populates="orders")
    items = relationship("OrderItemDB", back_populates="order")
    payment = relationship("PaymentDB", back_populates="order", uselist=False)
    complaints = relationship("ComplaintDB", back_populates="order")

class OrderItemDB(Base):
    __tablename__ = "order_items"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    item_name = Column(String)
    quantity = Column(Integer)
    price = Column(Float)
    
    order = relationship("OrderDB", back_populates="items")

class PaymentDB(Base):
    __tablename__ = "payments"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True)
    amount = Column(Float)
    payment_method = Column(String) # e.g. UPI, Credit Card, Cash
    status = Column(String) # e.g. Success, Pending, Failed
    
    order = relationship("OrderDB", back_populates="payment")

class ComplaintDB(Base):
    __tablename__ = "complaints"
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"))
    issue_description = Column(String)
    refund_issued = Column(Float, default=0.0)
    
    order = relationship("OrderDB", back_populates="complaints")
