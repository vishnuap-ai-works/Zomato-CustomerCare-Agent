from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents.factory import create_agent
import os
import logging
from agent.tools import get_tools_for_session

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("agent_core")

MODEL_TYPE = os.getenv("MODEL_TYPE", "openai").lower()

if MODEL_TYPE == "ollama":
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    llm = ChatOllama(model=ollama_model, base_url=ollama_base_url, temperature=0)
else:
    llm = ChatOpenAI(model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"), base_url='https://openai.vocareum.com/v1', temperature=0)

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
7. PROACTIVE: After addressing a customer's query, always proactively ask them a relevant follow-up question, such as "What can I help you with next?"
8. NO HALLUCINATION: You MUST ALWAYS use your provided tools to fetch real data (like orders, wallet balance, user details). NEVER make up or guess orders, prices, or statuses!
9. NO STALE DATA: Never reuse data from the chat history to answer queries about dynamic data (like current orders, balances, statuses). ALWAYS call the tool again to fetch the most up-to-date information.
"""

async def get_agent_executor(session_context: dict):
    is_authenticated = session_context.get("is_authenticated", False)
    if is_authenticated:
        auth_context = f"""
        User IS authenticated with mobile number: {session_context['mobile_number']}.
        DO NOT ask the user for their mobile number again.
        You can directly call order, payment, and subscription tools using this mobile number.
        """
    else:
        auth_context = """
        CRITICAL: The user is NOT authenticated. You currently ONLY have access to the `send_otp` and `verify_otp` tools.
        You CANNOT perform any actions regarding orders, payments, or account details until the user is authenticated.
        If the user asks for ANY account-related action (like checking an order, cancelling, getting refunds), you MUST immediately say:
        "I need to authenticate your account first. Could you please provide your mobile number?"
        DO NOT ask for order IDs or any other details until authentication is fully complete.
        - Step 1: Get mobile number.
        - Step 2: Use `send_otp`.
        - Step 3: Get OTP from user.
        - Step 4: Use `verify_otp`. Once verified, greet the user by name, confirm that they are authenticated, and ask how you can assist them with their request.
        IMPORTANT: NEVER claim or pretend that you have already cancelled an order, modified an order, processed a refund, or fetched account details in this step, because you do not have access to those tools until authentication is complete!
        """

    # Dynamically retrieve tools from the MCP server
    active_tools = await get_tools_for_session(is_authenticated)
    system_prompt = base_system_prompt.format(auth_context=auth_context)

    user_prompt = ChatPromptTemplate.from_messages([
        MessagesPlaceholder(variable_name="history"),
        ("user", "{input}")
    ])

    agent = create_agent(
        model=llm,
        tools=active_tools,
        system_prompt=system_prompt,
    )

    return agent, user_prompt

async def run_agent(input_text: str, history_messages: list, session_context: dict):
    logger.info(f"Initializing agent execution for session. Authenticated: {session_context.get('is_authenticated')}")
    agent, user_prompt = await get_agent_executor(session_context)

    prompt_val = user_prompt.invoke({"history": history_messages, "input": input_text})

    # Convert to dicts for agent.ainvoke
    messages_list = []
    for m in prompt_val.messages:
        role = "user" if m.type == "human" else "assistant"
        messages_list.append({"role": role, "content": m.content})

    try:
        logger.info(f"Invoking LLM asynchronously with {len(messages_list)} messages...")
        response = await agent.ainvoke({"messages": messages_list})
        logger.info("Agent invocation completed successfully.")
        return response
    except Exception as e:
        logger.error(f"Agent Execution Error: {str(e)}", exc_info=True)
        return {"messages": [{"content": f"Agent Error: {str(e)}"}]}
