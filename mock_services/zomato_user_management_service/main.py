from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from mock_services.data.database import init_db, get_db
from mock_services.data.models import CustomerDB
import logging
import time
from fastapi import Request

# Configure Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("user_management_service")

app = FastAPI(title="Zomato User Management Service")

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

class OTPRequest(BaseModel):
    mobile_number: str

class OTPVerifyRequest(BaseModel):
    mobile_number: str
    otp: str

@app.post("/send_otp")
def send_otp(req: OTPRequest, db: Session = Depends(get_db)):
    customer = db.query(CustomerDB).filter(CustomerDB.mobile_number == req.mobile_number).first()
    if not customer:
        logger.info(f"Creating new user on the fly for mobile number: {req.mobile_number}")
        customer = CustomerDB(mobile_number=req.mobile_number, name="Guest", mock_otp="1234")
        db.add(customer)
        db.commit()
    else:
        logger.info(f"OTP sent to existing user: {req.mobile_number}")
    return {"message": "OTP sent successfully. Hint: use 1234"}

@app.post("/verify_otp")
def verify_otp(req: OTPVerifyRequest, db: Session = Depends(get_db)):
    customer = db.query(CustomerDB).filter(CustomerDB.mobile_number == req.mobile_number).first()
    if customer and customer.mock_otp == req.otp:
        logger.info(f"OTP verified successfully for user: {req.mobile_number}")
        return {"status": "success", "message": f"OTP verified successfully. Tell the user they are authenticated and greet them with their name: {customer.name}."}
    
    logger.warning(f"Invalid OTP attempt for user: {req.mobile_number}")
    raise HTTPException(status_code=401, detail="Invalid OTP")

@app.get("/customer/{mobile_number}")
def get_customer(mobile_number: str, db: Session = Depends(get_db)):
    customer = db.query(CustomerDB).filter(CustomerDB.mobile_number == mobile_number).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {
        "name": customer.name,
        "mobile_number": customer.mobile_number,
        "has_subscription": customer.has_subscription,
        "subscription_expiry": customer.subscription_expiry
    }

class SubscriptionUpdate(BaseModel):
    has_subscription: bool

@app.post("/subscription/{mobile_number}/update")
def update_subscription(mobile_number: str, req: SubscriptionUpdate, db: Session = Depends(get_db)):
    customer = db.query(CustomerDB).filter(CustomerDB.mobile_number == mobile_number).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer.has_subscription = req.has_subscription
    if req.has_subscription:
        from datetime import datetime, timedelta
        customer.subscription_expiry = datetime.utcnow() + timedelta(days=30)
        logger.info(f"Subscription activated for user: {mobile_number}")
    else:
        customer.subscription_expiry = None
        logger.info(f"Subscription cancelled for user: {mobile_number}")
        
    db.commit()
    
    response_data = {"message": f"Subscription status updated to {req.has_subscription}"}
    if req.has_subscription:
        import uuid
        response_data["payment_link"] = f"https://zomato.mock/pay/sub_{uuid.uuid4().hex[:8]}"
        
    return response_data

class WalletAddRequest(BaseModel):
    amount: float

@app.get("/wallet/{mobile_number}")
def get_wallet_balance(mobile_number: str, db: Session = Depends(get_db)):
    customer = db.query(CustomerDB).filter(CustomerDB.mobile_number == mobile_number).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"wallet_balance": customer.wallet_balance}

@app.post("/wallet/{mobile_number}/add")
def add_to_wallet(mobile_number: str, req: WalletAddRequest, db: Session = Depends(get_db)):
    customer = db.query(CustomerDB).filter(CustomerDB.mobile_number == mobile_number).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    customer.wallet_balance += req.amount
    db.commit()
    logger.info(f"Added {req.amount} to wallet for {mobile_number}. New balance: {customer.wallet_balance}")
    return {"message": f"Successfully added {req.amount} to wallet. New balance: {customer.wallet_balance}", "new_balance": customer.wallet_balance}

