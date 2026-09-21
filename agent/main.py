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
    
    # Hook: Check if verify_otp was successfully called
    # The result contains the messages list from the agent execution
    if "messages" in result:
        for i, msg in enumerate(result["messages"]):
            if hasattr(msg, "name") and msg.name == "verify_otp" and "OTP verified successfully" in msg.content:
                # Find the AIMessage before this ToolMessage that contains the tool_call args
                # In Langchain, ToolMessage follows the AIMessage that requested it
                for prev_msg in reversed(result["messages"][:i]):
                    if hasattr(prev_msg, "tool_calls") and prev_msg.tool_calls:
                        for call in prev_msg.tool_calls:
                            if call["name"] == "verify_otp":
                                mobile_number = call["args"].get("mobile_number")
                                if mobile_number:
                                    update_session_auth(request.session_id, mobile_number)
                                    logger.info(f"Session {request.session_id} successfully authenticated for mobile {mobile_number}")
                                break

    # Extract final text
    final_response = "Sorry, I encountered an error."
    if "messages" in result and len(result["messages"]) > 0:
        last_msg = result["messages"][-1]
        if isinstance(last_msg, dict):
            final_response = last_msg.get("content", str(last_msg))
        else:
            final_response = last_msg.content
        
    return {"response": final_response}
