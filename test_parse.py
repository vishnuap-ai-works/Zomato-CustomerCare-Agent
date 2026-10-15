from langchain_core.messages import AIMessage, ToolMessage
from agent.session_manager import session_store, get_session, update_session_auth

def extract_text_content(content) -> str:
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                if "text" in item:
                    parts.append(str(item["text"]))
                else:
                    parts.append(str(item))
            else:
                parts.append(str(item))
        return " ".join(parts)
    return str(content) if content is not None else ""

def get_attr(msg, attr, default=None):
    if isinstance(msg, dict):
        return msg.get(attr, default)
    return getattr(msg, attr, default)

def process_messages(session_id, result):
    get_session(session_id)
    if "messages" in result:
        for i, msg in enumerate(result["messages"]):
            name = get_attr(msg, "name")
            content_text = extract_text_content(get_attr(msg, "content", ""))
            tool_call_id = get_attr(msg, "tool_call_id")
            if (name == "verify_otp" or "OTP verified successfully" in content_text) and "OTP verified successfully" in content_text:
                for prev_msg in reversed(result["messages"][:i]):
                    tool_calls = get_attr(prev_msg, "tool_calls")
                    if tool_calls:
                        found_auth = False
                        for call in tool_calls:
                            if (tool_call_id and call.get("id") == tool_call_id) or call.get("name") == "verify_otp":
                                mobile_number = call.get("args", {}).get("mobile_number")
                                if mobile_number:
                                    update_session_auth(session_id, str(mobile_number))
                                    found_auth = True
                                    break
                        if found_auth:
                            break

# Test 1: string content
res1 = {
    "messages": [
        AIMessage(content="", tool_calls=[{"name": "verify_otp", "args": {"mobile_number": "1234567890", "otp": "1234"}, "id": "call_1"}]),
        ToolMessage(content="OTP verified successfully. Tell the user...", name="verify_otp", tool_call_id="call_1")
    ]
}
process_messages("s1", res1)
assert session_store["s1"]["is_authenticated"] is True
assert session_store["s1"]["mobile_number"] == "1234567890"

# Test 2: MCP block list content
res2 = {
    "messages": [
        AIMessage(content="", tool_calls=[{"name": "verify_otp", "args": {"mobile_number": "9876543210", "otp": "1234"}, "id": "call_2"}]),
        ToolMessage(content=[{"type": "text", "text": "OTP verified successfully. Tell the user they are authenticated and greet them with their name: Alice Smith."}], name="verify_otp", tool_call_id="call_2")
    ]
}
process_messages("s2", res2)
assert session_store["s2"]["is_authenticated"] is True
assert session_store["s2"]["mobile_number"] == "9876543210"

print("All parsing tests passed successfully!")
