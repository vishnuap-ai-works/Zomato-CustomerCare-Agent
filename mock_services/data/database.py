import os
import random
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from mock_services.data.models import Base, CustomerDB, OrderDB, OrderItemDB, PaymentDB
from datetime import datetime, timedelta

import logging

# Configure logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("zomato_db")

# Create absolute path for SQLite DB to ensure it lives in mock_services/data/
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "zomato_mock.db")
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if data already exists
    if not db.query(CustomerDB).first():
        logger.info("Database is empty. Seeding mock database...")
        
        # Customers
        customers = [
            CustomerDB(mobile_number="1234567890", name="John Doe", has_subscription=True, subscription_expiry=datetime.utcnow() + timedelta(days=30), mock_otp="1234", wallet_balance=50.0),
            CustomerDB(mobile_number="9876543210", name="Alice Smith", has_subscription=False, subscription_expiry=None, mock_otp="1234", wallet_balance=15.5)
        ]
        db.add_all(customers)
        db.commit()
        
        # Orders for John Doe
        order1 = OrderDB(mobile_number="1234567890", restaurant="Pizza Hut", status="Delayed", delay_reason="Heavy rain", address="123 Main St", driver_eta="15 mins", driver_location="Main St")
        order2 = OrderDB(mobile_number="1234567890", restaurant="Burger King", status="Preparing", address="123 Main St")
        order3 = OrderDB(mobile_number="1234567890", restaurant="Starbucks", status="Delivered", address="123 Main St")
        
        # Orders for Alice Smith
        order4 = OrderDB(mobile_number="9876543210", restaurant="KFC", status="Out for Delivery", address="456 Elm St", driver_eta="5 mins", driver_location="Elm St")
        order5 = OrderDB(mobile_number="9876543210", restaurant="Subway", status="Cancelled", address="456 Elm St", refund_status="Pending Bank Settlement")
        
        db.add_all([order1, order2, order3, order4, order5])
        db.commit()
        
        # Items and Payments for John Doe's Orders
        db.add_all([
            OrderItemDB(order_id=order1.id, item_name="Pepperoni Pizza", quantity=1, price=15.99),
            OrderItemDB(order_id=order1.id, item_name="Garlic Bread", quantity=2, price=4.99),
            PaymentDB(order_id=order1.id, amount=25.97, payment_method="Credit Card", status="Success"),
            
            OrderItemDB(order_id=order2.id, item_name="Whopper", quantity=2, price=8.50),
            PaymentDB(order_id=order2.id, amount=17.00, payment_method="UPI", status="Success"),
            
            OrderItemDB(order_id=order3.id, item_name="Caramel Macchiato", quantity=1, price=5.50),
            OrderItemDB(order_id=order3.id, item_name="Croissant", quantity=1, price=3.50),
            PaymentDB(order_id=order3.id, amount=9.00, payment_method="Wallet", status="Success")
        ])
        
        # Items and Payments for Alice Smith's Orders
        db.add_all([
            OrderItemDB(order_id=order4.id, item_name="Zinger Burger Combo", quantity=1, price=12.99),
            PaymentDB(order_id=order4.id, amount=12.99, payment_method="Credit Card", status="Success"),
            
            OrderItemDB(order_id=order5.id, item_name="Footlong Italian BMT", quantity=1, price=10.00),
            PaymentDB(order_id=order5.id, amount=10.00, payment_method="UPI", status="Refunded")
        ])
        
        db.commit()
        logger.info("Mock database seeded successfully with customers, orders, items, and payments.")
    
    db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
