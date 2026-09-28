from langchain_core.messages import AIMessage, ToolMessage
from agent.session_manager import session_store, get_session
from typing import List
import copy

messages = [
    AIMessage(content="", tool_calls=[{"name": "verify_otp", "args": {"mobile_number": "1234567890", "otp": "1234"}, "id": "call_1"}]),
    ToolMessage(content="OTP verified successfully. Tell the user...", name="verify_otp", tool_call_id="call_1")
]

result = {"messages": messages}
session_id = "test_session"
get_session(session_id)

if "messages" in result:
    for i, msg in enumerate(result["messages"]):
        if hasattr(msg, "name") and msg.name == "verify_otp" and "OTP verified successfully" in msg.content:
            for prev_msg in reversed(result["messages"][:i]):
                if hasattr(prev_msg, "tool_calls") and prev_msg.tool_calls:
                    for call in prev_msg.tool_calls:
                        if call["name"] == "verify_otp":
                            mobile_number = call["args"].get("mobile_number")
                            if mobile_number:
                                from agent.session_manager import update_session_auth
                                update_session_auth(session_id, mobile_number)
                                print(f"Session {session_id} successfully authenticated for mobile {mobile_number}")
                            break

print(session_store[session_id])
