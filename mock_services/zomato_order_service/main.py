from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from mock_services.data.database import init_db, get_db
from mock_services.data.database import init_db, get_db
from mock_services.data.models import OrderDB, OrderItemDB, PaymentDB
import logging
import time
from fastapi import Request

# Configure Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("order_service")

app = FastAPI(title="Zomato Order Service")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - Latency: {process_time:.2f}ms")
    return response

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/orders/{mobile_number}")
def get_orders(mobile_number: str, active_only: bool = False, db: Session = Depends(get_db)):
    query = db.query(OrderDB).filter(OrderDB.mobile_number == mobile_number)
    if active_only:
        query = query.filter(OrderDB.status.notin_(["Delivered", "Cancelled"]))
    orders = query.all()
    if not orders:
        return {"orders": []}
    return {"orders": [
        {
            "id": o.id,
            "restaurant": o.restaurant,
            "status": o.status,
            "delay_reason": o.delay_reason,
            "address": o.address,
            "created_at": o.created_at
        } for o in orders
    ]}

@app.get("/order/{order_id}/items")
def get_order_items(order_id: int, db: Session = Depends(get_db)):
    items = db.query(OrderItemDB).filter(OrderItemDB.order_id == order_id).all()
    if not items:
        return {"items": []}
    return {"items": [
        {"item_name": i.item_name, "quantity": i.quantity, "price": i.price} for i in items
    ]}

@app.get("/order/{order_id}/payment")
def get_order_payment(order_id: int, db: Session = Depends(get_db)):
    payment = db.query(PaymentDB).filter(PaymentDB.order_id == order_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {
        "amount": payment.amount,
        "payment_method": payment.payment_method,
        "status": payment.status
    }

@app.post("/order/{order_id}/cancel")
def cancel_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status in ["Delivered", "Cancelled"]:
        logger.warning(f"Failed to cancel order {order_id}. Current status: {order.status}")
        return {"message": f"Cannot cancel order. It is already {order.status}."}
    
    order.status = "Cancelled"
    db.commit()
    logger.info(f"Order {order_id} successfully cancelled.")
    return {"message": "Order cancelled successfully."}

class AddressUpdate(BaseModel):
    new_address: str

@app.post("/order/{order_id}/address")
def update_order_address(order_id: int, req: AddressUpdate, db: Session = Depends(get_db)):
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status in ["Delivered", "Cancelled"]:
        return {"message": f"Cannot change address. The order is already {order.status}."}
    
    order.address = req.new_address
    db.commit()
    return {"message": f"Delivery address updated successfully to: {req.new_address}"}

@app.get("/order/{order_id}/driver")
def get_driver_info(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if not order.driver_eta:
        return {"message": "No driver assigned or order is not active."}
    return {
        "eta": order.driver_eta,
        "location": order.driver_location,
        "instruction": order.driver_instruction
    }

class DriverInstruction(BaseModel):
    instruction: str

@app.post("/order/{order_id}/driver/contact")
def contact_driver(order_id: int, req: DriverInstruction, db: Session = Depends(get_db)):
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order or not order.driver_eta:
        raise HTTPException(status_code=404, detail="No active driver to contact.")
    order.driver_instruction = req.instruction
    db.commit()
    logger.info(f"Sent driver instruction for order {order_id}: {req.instruction}")
    return {"message": f"Driver has been notified: '{req.instruction}'"}

@app.get("/order/{order_id}/refund")
def get_refund_status(order_id: int, db: Session = Depends(get_db)):
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if not order.refund_status:
        return {"message": "No refund initiated for this order."}
    return {"refund_status": order.refund_status}

class ComplaintRequest(BaseModel):
    issue_description: str

from mock_services.data.models import ComplaintDB, CustomerDB

@app.post("/order/{order_id}/complaint")
def file_complaint(order_id: int, req: ComplaintRequest, db: Session = Depends(get_db)):
    order = db.query(OrderDB).filter(OrderDB.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # We will automatically issue a 10.0 refund for any complaint for mock purposes
    refund_amount = 10.0
    
    complaint = ComplaintDB(order_id=order_id, issue_description=req.issue_description, refund_issued=refund_amount)
    db.add(complaint)
    
    # Update customer wallet
    customer = db.query(CustomerDB).filter(CustomerDB.mobile_number == order.mobile_number).first()
    if customer:
        customer.wallet_balance += refund_amount
        logger.info(f"Automated refund of {refund_amount} deposited into customer {order.mobile_number}'s wallet.")
        
    db.commit()
    logger.info(f"Complaint filed successfully for order {order_id}.")
    return {
        "message": "Complaint filed successfully.",
        "refund_issued": refund_amount,
        "new_wallet_balance": customer.wallet_balance if customer else None
    }

