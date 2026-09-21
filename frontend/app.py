import streamlit as st
import requests
import os
import uuid

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Zomato Customer Care", page_icon="🍔", layout="centered")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

st.title("🍔 Zomato AI Support")
st.write("Welcome! Feel free to ask me anything about your Zomato orders.")

if st.button("Clear Chat"):
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("How can I help you today?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
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
                agent_response = response.json()["response"]
                message_placeholder.markdown(agent_response)
                st.session_state.messages.append({"role": "assistant", "content": agent_response})
            else:
                st.error(f"Backend error: {response.text}")
        except Exception as e:
            st.error(f"Failed to connect to backend API: {e}")
