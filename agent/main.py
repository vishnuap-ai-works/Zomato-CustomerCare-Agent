from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from langchain_core.messages import HumanMessage, AIMessage
from agent.agent import run_agent
from agent.session_manager import get_session, update_session_auth
import logging
import time
from fastapi import Request

# Configure Logger
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("agent_gateway")

app = FastAPI(title="Zomato Agent Service")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    logger.info(f"{request.method} {request.url.path} - Status: {response.status_code} - Latency: {process_time:.2f}ms")
    return response

class ChatRequest(BaseModel):
    session_id: str
    message: str
    history: List[dict] = []

class ClearChatRequest(BaseModel):
    session_id: str

@app.post("/api/chat")
def chat(request: ChatRequest):
    logger.info(f"Incoming chat message for session {request.session_id}")
    # Manage session
    session_context = get_session(request.session_id)
    
    # Convert history
    messages = []
    for msg in request.history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))
            
    # Run Agent
    result = run_agent(request.message, messages, session_context)
    
    tool_calls_info = []

    def get_attr(msg, attr, default=None):
        if isinstance(msg, dict):
            return msg.get(attr, default)
        return getattr(msg, attr, default)

    if "messages" in result:
        # Find index of last human message
        last_human_idx = 0
        for i, msg in enumerate(result["messages"]):
            role = get_attr(msg, "role") or get_attr(msg, "type")
            if role in ["user", "human"]:
                last_human_idx = i
                
        # Extract tool calls from the current request
        for i in range(last_human_idx + 1, len(result["messages"])):
            msg = result["messages"][i]
            tool_calls = get_attr(msg, "tool_calls")
            if tool_calls:
                for call in tool_calls:
                    tool_calls_info.append({"name": call.get("name"), "args": call.get("args", {})})

        # Hook: Check if verify_otp was successfully called
        for i, msg in enumerate(result["messages"]):
            name = get_attr(msg, "name")
            content = get_attr(msg, "content", "")
            if name == "verify_otp" and content and "OTP verified successfully" in content:
                # Find the AIMessage before this ToolMessage that contains the tool_call args
                for prev_msg in reversed(result["messages"][:i]):
                    tool_calls = get_attr(prev_msg, "tool_calls")
                    if tool_calls:
                        for call in tool_calls:
                            if call.get("name") == "verify_otp":
                                mobile_number = call.get("args", {}).get("mobile_number")
                                if mobile_number:
                                    update_session_auth(request.session_id, mobile_number)
                                    logger.info(f"Session {request.session_id} successfully authenticated for mobile {mobile_number}")
                                break

    # Extract final text
    final_response = "Sorry, I encountered an error."
    if "messages" in result and len(result["messages"]) > 0:
        last_msg = result["messages"][-1]
        final_response = get_attr(last_msg, "content", str(last_msg))
        
    return {"response": final_response, "tool_calls": tool_calls_info}

@app.post("/api/clear_chat")
def clear_chat(request: ClearChatRequest):
    logger.info(f"Clearing chat and authentication for session {request.session_id}")
    from agent.session_manager import session_store
    if request.session_id in session_store:
        # Reset the session state
        session_store[request.session_id]["is_authenticated"] = False
        session_store[request.session_id]["mobile_number"] = None
    return {"status": "success", "message": "Session cleared"}
