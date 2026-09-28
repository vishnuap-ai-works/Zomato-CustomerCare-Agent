import streamlit as st
import requests
import os
import uuid

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Zomato Customer Care", page_icon="💬", layout="centered")

from datetime import datetime

# Custom CSS for Microsoft Teams Design (Dark Theme)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap');
    
    /* Global Font and Dark Background */
    html, body, [class*="css"]  {
        font-family: 'Segoe UI', system-ui, sans-serif !important;
        background-color: #1f1f1f !important;
        color: #e0e0e0 !important;
    }
    
    .stApp {
        background-color: #1f1f1f !important;
    }
    
    .stApp > header {
        background-color: transparent !important;
    }
    
    /* Chat Input Styling */
    [data-testid="stChatInput"] {
        border-radius: 6px !important;
        border: 1px solid #3b3b3b !important;
        background-color: #292929 !important;
    }
    [data-testid="stChatInput"] textarea {
        color: #e0e0e0 !important;
    }
    [data-testid="stChatInput"] svg {
        fill: #e0e0e0 !important;
    }
    [data-testid="stChatInput"]:focus-within {
        border-color: #5B5FC7 !important;
    }
    
    /* Buttons */
    .stButton > button {
        background-color: #292929 !important;
        color: #e0e0e0 !important;
        border: 1px solid #3b3b3b !important;
        border-radius: 4px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background-color: #333333 !important;
        border-color: #5B5FC7 !important;
    }
    
    /* Title */
    h1 {
        color: #e0e0e0 !important;
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        border-bottom: 2px solid #3b3b3b;
        padding-bottom: 10px;
    }
    
    /* Expander */
    [data-testid="stExpander"] {
        background-color: #292929 !important;
        border: 1px solid #3b3b3b !important;
        border-radius: 4px !important;
    }
    [data-testid="stExpander"] summary {
        color: #e0e0e0 !important;
    }
    code {
        color: #e0e0e0 !important;
        background-color: #1f1f1f !important;
    }
</style>
""", unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

st.title("💬 Zomato AI Support")
st.markdown("**Welcome!** Feel free to ask me anything about your Zomato orders.")

if st.button("Clear Chat"):
    try:
        requests.post(f"{BACKEND_URL}/api/clear_chat", json={"session_id": st.session_state.session_id})
    except Exception as e:
        st.error(f"Failed to clear backend session: {e}")
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.rerun()

def render_message(role, content):
    timestamp = datetime.now().strftime("%d/%m %I:%M %p").lower()
    if role == "user":
        st.markdown(f"""
        <div style="display: flex; flex-direction: column; align-items: flex-end; margin-bottom: 8px;">
            <div style="font-size: 11px; color: #8a8a8a; margin-bottom: 4px; margin-right: 4px;">
                {timestamp}
            </div>
            <div style="background-color: #3b3a59; color: #e0e0e0; padding: 10px 14px; border-radius: 4px; max-width: 75%; font-family: 'Segoe UI', sans-serif; font-size: 14px; line-height: 1.4;">
                {content}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="display: flex; flex-direction: column; align-items: flex-start; margin-bottom: 12px;">
            <div style="font-size: 11px; color: #8a8a8a; margin-bottom: 4px; margin-left: 44px;">
                Zomato AI Support &nbsp; {timestamp}
            </div>
            <div style="display: flex; flex-direction: row; align-items: flex-start; width: 100%;">
                <div style="width: 32px; height: 32px; border-radius: 50%; background-color: #e23744; color: white; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: bold; margin-right: 12px; flex-shrink: 0; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                    Z
                </div>
                <div style="background-color: #292929; color: #e0e0e0; padding: 10px 14px; border-radius: 4px; max-width: 75%; font-family: 'Segoe UI', sans-serif; font-size: 14px; line-height: 1.4;">
                    {content}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg["role"] == "assistant" and msg.get("tool_calls"):
        with st.expander("🛠️ Tool Calls (Agent Processing)"):
            for call in msg["tool_calls"]:
                st.code(f"{call['name']}({call.get('args', {})})")
    render_message(msg["role"], msg["content"])

if prompt := st.chat_input("Type a new message..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    render_message("user", prompt)

    message_placeholder = st.empty()
    message_placeholder.markdown("Thinking...")
    
    try:
        # Prepare history for the backend
        history = [{"role": m["role"], "content": m["content"]} for m in st.session_state.messages[:-1]]
        
        response = requests.post(f"{BACKEND_URL}/api/chat", json={
            "session_id": st.session_state.session_id,
            "message": prompt,
            "history": history
        })
        
        if response.status_code == 200:
            data = response.json()
            agent_response = data.get("response", "Error getting response.")
            tool_calls = data.get("tool_calls", [])
            
            message_placeholder.empty()
            
            if tool_calls:
                with st.expander("🛠️ Tool Calls (Agent Processing)"):
                    for call in tool_calls:
                        st.code(f"{call['name']}({call.get('args', {})})")
            
            render_message("assistant", agent_response)
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": agent_response,
                "tool_calls": tool_calls
            })
        else:
            message_placeholder.empty()
            st.error(f"Backend error: {response.text}")
    except Exception as e:
        message_placeholder.empty()
        st.error(f"Failed to connect to backend API: {e}")
