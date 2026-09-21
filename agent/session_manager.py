from datetime import datetime, timedelta

# In-memory session store
# Format: { "session_id": {"mobile_number": str, "is_authenticated": bool, "last_activity": datetime} }
session_store = {}

SESSION_TIMEOUT_MINUTES = 5

def get_session(session_id: str) -> dict:
    now = datetime.utcnow()
    
    if session_id not in session_store:
        session_store[session_id] = {
            "mobile_number": None,
            "is_authenticated": False,
            "last_activity": now
        }
        return session_store[session_id]
    
    session = session_store[session_id]
    
    # Check timeout
    if session["is_authenticated"]:
        if (now - session["last_activity"]) > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
            print(f"Session {session_id} timed out.")
            session["is_authenticated"] = False
            session["mobile_number"] = None
    
    # Update last activity
    session["last_activity"] = now
    return session

def update_session_auth(session_id: str, mobile_number: str):
    if session_id in session_store:
        session_store[session_id]["mobile_number"] = mobile_number
        session_store[session_id]["is_authenticated"] = True
        session_store[session_id]["last_activity"] = datetime.utcnow()
