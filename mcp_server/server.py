import os
import requests
import logging
from starlette.responses import JSONResponse
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("mcp_server")

# Backend Service URLs
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user_management:8002")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order_service:8001")

# Initialize FastMCP Server
mcp = FastMCP(
    "zomato_customer_care_mcp",
    host="0.0.0.0",
    port=int(os.getenv("PORT", "8003")),
)

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    return JSONResponse({"status": "healthy", "service": "zomato_mcp_server"})

# --- Authentication & User Tools ---

@mcp.tool()
def send_otp(mobile_number: str) -> str:
    """Sends an OTP to the user's mobile number for authentication. Call this ONLY if the user is NOT authenticated yet."""
    logger.info(f"MCP executing send_otp for mobile: {mobile_number}")
    try:
        response = requests.post(f"{USER_SERVICE_URL}/send_otp", json={"mobile_number": mobile_number})
        return response.json().get("message", "OTP sent successfully.")
    except Exception as e:
        logger.error(f"Failed to send OTP: {str(e)}")
        return f"Failed to send OTP: {str(e)}"

@mcp.tool()
def verify_otp(mobile_number: str, otp: str) -> str:
    """Verifies the OTP provided by the user. Must be called after send_otp."""
    logger.info(f"MCP executing verify_otp for mobile: {mobile_number}")
    try:
        response = requests.post(f"{USER_SERVICE_URL}/verify_otp", json={"mobile_number": mobile_number, "otp": otp})
        if response.status_code == 200:
            return response.json().get("message", "OTP verified successfully. The user is now authenticated.")
        else:
            return "Invalid OTP. Authentication failed."
    except Exception as e:
        logger.error(f"Failed to verify OTP: {str(e)}")
        return f"Failed to verify OTP: {str(e)}"

@mcp.tool()
def get_customer_details(mobile_number: str) -> str:
    """Gets customer profile details."""
    logger.info(f"MCP executing get_customer_details for mobile: {mobile_number}")
    try:
        response = requests.get(f"{USER_SERVICE_URL}/customer/{mobile_number}")
        if response.status_code == 200:
            return str(response.json())
        return "Customer not found."
    except Exception as e:
        logger.error(f"Failed to get customer details: {str(e)}")
        return str(e)

@mcp.tool()
def update_subscription(mobile_number: str, has_subscription: bool) -> str:
    """Updates the subscription status for the user."""
    logger.info(f"MCP executing update_subscription for mobile: {mobile_number}, status: {has_subscription}")
    try:
        response = requests.post(f"{USER_SERVICE_URL}/subscription/{mobile_number}/update", json={"has_subscription": has_subscription})
        if response.status_code == 200:
            return str(response.json())
        return "Failed to update subscription."
    except Exception as e:
        logger.error(f"Failed to update subscription: {str(e)}")
        return str(e)

@mcp.tool()
def get_wallet_balance(mobile_number: str) -> str:
    """Gets the user's current wallet balance."""
    logger.info(f"MCP executing get_wallet_balance for mobile: {mobile_number}")
    try:
        response = requests.get(f"{USER_SERVICE_URL}/wallet/{mobile_number}")
        if response.status_code == 200:
            return str(response.json())
        return "Failed to fetch wallet balance."
    except Exception as e:
        logger.error(f"Failed to fetch wallet balance: {str(e)}")
        return str(e)

# --- Order & Delivery Tools ---

@mcp.tool()
def get_orders(mobile_number: str, active_only: bool = False) -> str:
    """Gets orders for the authenticated user. Set active_only=True to get only active/ongoing orders."""
    logger.info(f"MCP executing get_orders for mobile: {mobile_number}, active_only: {active_only}")
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/orders/{mobile_number}?active_only={str(active_only).lower()}")
        if response.status_code == 200:
            return str(response.json())
        return "Failed to fetch orders."
    except Exception as e:
        logger.error(f"Failed to fetch orders: {str(e)}")
        return str(e)

@mcp.tool()
def get_order_details(order_id: int) -> str:
    """Gets the complete details of a specific order (status, restaurant, delay reason, address, etc)."""
    logger.info(f"MCP executing get_order_details for order: {order_id}")
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/order/{order_id}")
        if response.status_code == 200:
            return str(response.json())
        return "Failed to fetch order details."
    except Exception as e:
        logger.error(f"Failed to fetch order details: {str(e)}")
        return str(e)

@mcp.tool()
def get_order_items(order_id: int) -> str:
    """Gets the items inside a specific order."""
    logger.info(f"MCP executing get_order_items for order: {order_id}")
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/order/{order_id}/items")
        if response.status_code == 200:
            return str(response.json())
        return "Failed to fetch order items."
    except Exception as e:
        logger.error(f"Failed to fetch order items: {str(e)}")
        return str(e)

@mcp.tool()
def get_payment_details(order_id: int) -> str:
    """Gets payment details for a specific order."""
    logger.info(f"MCP executing get_payment_details for order: {order_id}")
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/order/{order_id}/payment")
        if response.status_code == 200:
            return str(response.json())
        return "Failed to fetch payment details."
    except Exception as e:
        logger.error(f"Failed to fetch payment details: {str(e)}")
        return str(e)

@mcp.tool()
def cancel_order(order_id: int) -> str:
    """Cancels a specific order."""
    logger.info(f"MCP executing cancel_order for order: {order_id}")
    try:
        response = requests.post(f"{ORDER_SERVICE_URL}/order/{order_id}/cancel")
        if response.status_code == 200:
            return str(response.json())
        return "Failed to cancel order."
    except Exception as e:
        logger.error(f"Failed to cancel order: {str(e)}")
        return str(e)

@mcp.tool()
def update_order_address(order_id: int, new_address: str) -> str:
    """Updates the delivery address for a specific order."""
    logger.info(f"MCP executing update_order_address for order: {order_id}")
    try:
        response = requests.post(f"{ORDER_SERVICE_URL}/order/{order_id}/address", json={"new_address": new_address})
        if response.status_code == 200:
            return str(response.json())
        return "Failed to update order address."
    except Exception as e:
        logger.error(f"Failed to update order address: {str(e)}")
        return str(e)

@mcp.tool()
def check_refund_status(order_id: int) -> str:
    """Checks the refund status of a cancelled or compensated order."""
    logger.info(f"MCP executing check_refund_status for order: {order_id}")
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/order/{order_id}/refund")
        if response.status_code == 200:
            return str(response.json())
        return "Failed to fetch refund status."
    except Exception as e:
        logger.error(f"Failed to check refund status: {str(e)}")
        return str(e)

@mcp.tool()
def track_driver(order_id: int) -> str:
    """Gets the live location and ETA of the delivery partner."""
    logger.info(f"MCP executing track_driver for order: {order_id}")
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/order/{order_id}/driver")
        if response.status_code == 200:
            return str(response.json())
        return "Failed to track driver."
    except Exception as e:
        logger.error(f"Failed to track driver: {str(e)}")
        return str(e)

@mcp.tool()
def contact_delivery_partner(order_id: int, message: str) -> str:
    """Sends an SMS instruction/message to the delivery partner."""
    logger.info(f"MCP executing contact_delivery_partner for order: {order_id}")
    try:
        response = requests.post(f"{ORDER_SERVICE_URL}/order/{order_id}/driver/contact", json={"instruction": message})
        if response.status_code == 200:
            return str(response.json())
        return "Failed to contact driver."
    except Exception as e:
        logger.error(f"Failed to contact driver: {str(e)}")
        return str(e)

@mcp.tool()
def file_order_complaint(order_id: int, issue_details: str) -> str:
    """Files a complaint for an order (e.g., missing items, bad quality) and automatically processes a refund."""
    logger.info(f"MCP executing file_order_complaint for order: {order_id}")
    try:
        response = requests.post(f"{ORDER_SERVICE_URL}/order/{order_id}/complaint", json={"issue_description": issue_details})
        if response.status_code == 200:
            return str(response.json())
        return "Failed to file complaint."
    except Exception as e:
        logger.error(f"Failed to file complaint: {str(e)}")
        return str(e)

# ASGI Application for SSE
app = mcp.sse_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mcp_server.server:app", host="0.0.0.0", port=int(os.getenv("PORT", "8003")), reload=False)
