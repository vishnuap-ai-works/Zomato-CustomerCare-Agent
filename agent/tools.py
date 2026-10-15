import os
import logging
from langchain_mcp_adapters.client import MultiServerMCPClient

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("agent_mcp_client")

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://mcp_server:8003/sse")

logger.info(f"Configuring Agent MCP client pointing to: {MCP_SERVER_URL}")

mcp_client = MultiServerMCPClient({
    "zomato_mcp": {
        "transport": "sse",
        "url": MCP_SERVER_URL
    }
})

_tools_cache = None

async def get_all_tools(force_refresh: bool = False):
    """Fetches all tools from the remote MCP server via SSE transport."""
    global _tools_cache
    if _tools_cache is None or force_refresh:
        logger.info(f"Fetching tools dynamically from MCP server at {MCP_SERVER_URL}...")
        _tools_cache = await mcp_client.get_tools()
        logger.info(f"Successfully loaded {len(_tools_cache)} tools from MCP: {[t.name for t in _tools_cache]}")
    return _tools_cache

async def get_tools_for_session(is_authenticated: bool):
    """Returns tools filtered by authentication state."""
    tools = await get_all_tools()
    if is_authenticated:
        return tools
    # When unauthenticated, only OTP authentication tools are permitted
    return [t for t in tools if t.name in ["send_otp", "verify_otp"]]
