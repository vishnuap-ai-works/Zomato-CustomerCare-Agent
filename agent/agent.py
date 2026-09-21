from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.factory import create_agent
import os
import logging
from agent.tools import get_all_tools

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("agent_core")

tools = get_all_tools()

MODEL_TYPE = os.getenv("MODEL_TYPE", "openai").lower()

if MODEL_TYPE == "ollama":
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    llm = ChatOllama(model=ollama_model, base_url=ollama_base_url, temperature=0)
else:
    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), temperature=0)

base_system_prompt = """You are a highly capable and proactive Zomato Customer Care Agent.
You assist customers with live status updates, delay reasons, address modifications, missing items, quality complaints, cancellations, and subscriptions.

CRITICAL RULES:
1. OUT OF DOMAIN: If a user asks a question that goes beyond the Zomato domain, simply say "I can't answer that".
2. GREETINGS: Normal greetings should be responded to politely.
3. SUBSCRIPTIONS: If a user asks about their subscription and it is inactive, expired, or they don't have one, you MUST proactively call the `update_subscription` tool to renew or enable it (which generates a payment link for them).
4. COMPLAINTS & REFUNDS: If a user complains about missing items or bad quality, empathize and immediately use `file_order_complaint`. Inform them of any automated refund issued to their wallet.
5. DRIVER TRACKING: If a user asks where their order is, use `track_driver` and provide the ETA. Offer to `contact_delivery_partner` if they have special instructions.
6. AUTHENTICATION (CRITICAL):
{auth_context}
5. PROACTIVE: After addressing a customer's query, always proactively ask them a relevant follow-up question, such as "What can I help you with next?"
"""

def get_agent_executor(session_context: dict):
    # Dynamically build system prompt based on session
    if session_context.get("is_authenticated"):
        auth_context = f"""
        User IS authenticated with mobile number: {session_context['mobile_number']}.
        DO NOT ask the user for their mobile number again.
        You can directly call order, payment, and subscription tools using this mobile number.
        """
    else:
        auth_context = """
        User is NOT authenticated.
        If they ask a question requiring account access (like "Where is my order?"), you MUST:
        - Ask for their mobile number.
        - Use the `send_otp` tool.
        - Ask the user for the OTP.
        - Use the `verify_otp` tool.
        Only after successful verification can you use other tools.
        """
        
    system_prompt = base_system_prompt.format(auth_context=auth_context)
    
    user_prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="history"),
        ("user", "{input}")
    ])
    
    agent = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
    )
    
    return agent, user_prompt

def run_agent(input_text: str, history_messages: list, session_context: dict):
    logger.info(f"Initializing agent execution for session. Authenticated: {session_context.get('is_authenticated')}")
    agent, user_prompt = get_agent_executor(session_context)
    
    prompt_val = user_prompt.invoke({"history": history_messages, "input": input_text})
    
    # Convert to dicts for agent.invoke
    messages_list = []
    for m in prompt_val.messages:
        role = "user" if m.type == "human" else "assistant"
        messages_list.append({"role": role, "content": m.content})
        
    try:
        logger.info(f"Invoking LLM with {len(messages_list)} messages...")
        response = agent.invoke({"messages": messages_list})
        logger.info("Agent invocation completed successfully.")
        
        # Check if the agent successfully called verify_otp
        # Langchain agent.invoke returns intermediate steps or we can just infer from the response.
        # But a safer way is if the user successfully verified, the response text might indicate it.
        # However, a robust way is to hook the verify_otp tool. We'll handle this in main.py by parsing the output or just letting the frontend send the mobile number if it gets it.
        # Wait, if the tool runs in the agent, the agent just gets the string "OTP verified successfully."
        # We can scan the agent's messages to see if that string is in it.
        
        for msg in response.get("messages", []):
            if hasattr(msg, 'content') and "OTP verified successfully" in msg.content:
                # We need to extract the mobile number they verified.
                # It's in the tool call arguments. We will just return a flag to main.py to handle it.
                pass
                
        return response
    except Exception as e:
        logger.error(f"Agent Execution Error: {str(e)}", exc_info=True)
        return {"messages": [{"content": f"Agent Error: {str(e)}"}]}
