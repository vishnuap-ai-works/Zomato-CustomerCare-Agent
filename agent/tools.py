import os
import requests
import logging
from langchain_core.tools import tool

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("agent_tools")

# Tracing network calls made by tools
_original_get = requests.get
_original_post = requests.post

def _logged_get(url, **kwargs):
    logger.info(f"Tool executing HTTP GET: {url}")
    return _original_get(url, **kwargs)

def _logged_post(url, **kwargs):
    logger.info(f"Tool executing HTTP POST: {url} with payload {kwargs.get('json', {})}")
    return _original_post(url, **kwargs)

requests.get = _logged_get
requests.post = _logged_post

USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user_management:8002")
ORDER_SERVICE_URL = os.getenv("ORDER_SERVICE_URL", "http://order_service:8001")

@tool
def send_otp(mobile_number: str) -> str:
    """Sends an OTP to the user's mobile number for authentication. Always call this when a user wants to access their account."""
    try:
        response = requests.post(f"{USER_SERVICE_URL}/send_otp", json={"mobile_number": mobile_number})
        return response.json().get("message", "OTP sent successfully.")
    except Exception as e:
        return f"Failed to send OTP: {str(e)}"

# Note: verify_otp is handled specially in agent.py because it needs to update the session.
# We will define a standard tool here that just calls the API, but the agent's wrapper will hook it.
@tool
def verify_otp(mobile_number: str, otp: str) -> str:
    """Verifies the OTP provided by the user. Must be called after send_otp."""
    try:
        response = requests.post(f"{USER_SERVICE_URL}/verify_otp", json={"mobile_number": mobile_number, "otp": otp})
        if response.status_code == 200:
            return response.json().get("message", "OTP verified successfully. The user is now authenticated.")
        else:
            return "Invalid OTP. Authentication failed."
    except Exception as e:
        return f"Failed to verify OTP: {str(e)}"

@tool
def get_customer_details(mobile_number: str) -> str:
    """Gets customer profile details."""
    try:
        response = requests.get(f"{USER_SERVICE_URL}/customer/{mobile_number}")
        if response.status_code == 200:
            return str(response.json())
        return "Customer not found."
    except Exception as e:
        return str(e)

@tool
def get_orders(mobile_number: str, active_only: bool = False) -> str:
    """Gets orders for the authenticated user. Set active_only=True to get only active/ongoing orders."""
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/orders/{mobile_number}?active_only={str(active_only).lower()}")
        if response.status_code == 200:
            return str(response.json())
        return "Failed to fetch orders."
    except Exception as e:
        return str(e)

@tool
def get_order_items(order_id: int) -> str:
    """Gets the items inside a specific order."""
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/order/{order_id}/items")
        if response.status_code == 200:
            return str(response.json())
        return "Failed to fetch order items."
    except Exception as e:
        return str(e)

@tool
def get_payment_details(order_id: int) -> str:
    """Gets payment details for a specific order."""
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/order/{order_id}/payment")
        if response.status_code == 200:
            return str(response.json())
        return "Failed to fetch payment details."
    except Exception as e:
        return str(e)

@tool
def cancel_order(order_id: int) -> str:
    """Cancels a specific order."""
    try:
        response = requests.post(f"{ORDER_SERVICE_URL}/order/{order_id}/cancel")
        if response.status_code == 200:
            return str(response.json())
        return "Failed to cancel order."
    except Exception as e:
        return str(e)

@tool
def update_subscription(mobile_number: str, has_subscription: bool) -> str:
    """Updates the subscription status for the user."""
    try:
        response = requests.post(f"{USER_SERVICE_URL}/subscription/{mobile_number}/update", json={"has_subscription": has_subscription})
        if response.status_code == 200:
            return str(response.json())
        return "Failed to update subscription."
    except Exception as e:
        return str(e)

@tool
def update_order_address(order_id: int, new_address: str) -> str:
    """Updates the delivery address for a specific order."""
    try:
        response = requests.post(f"{ORDER_SERVICE_URL}/order/{order_id}/address", json={"new_address": new_address})
        if response.status_code == 200:
            return str(response.json())
        return "Failed to update order address."
    except Exception as e:
        return str(e)

@tool
def get_wallet_balance(mobile_number: str) -> str:
    """Gets the user's current wallet balance."""
    try:
        response = requests.get(f"{USER_SERVICE_URL}/wallet/{mobile_number}")
        if response.status_code == 200:
            return str(response.json())
        return "Failed to fetch wallet balance."
    except Exception as e:
        return str(e)

@tool
def check_refund_status(order_id: int) -> str:
    """Checks the refund status of a cancelled or compensated order."""
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/order/{order_id}/refund")
        if response.status_code == 200:
            return str(response.json())
        return "Failed to fetch refund status."
    except Exception as e:
        return str(e)

@tool
def track_driver(order_id: int) -> str:
    """Gets the live location and ETA of the delivery partner."""
    try:
        response = requests.get(f"{ORDER_SERVICE_URL}/order/{order_id}/driver")
        if response.status_code == 200:
            return str(response.json())
        return "Failed to track driver."
    except Exception as e:
        return str(e)

@tool
def contact_delivery_partner(order_id: int, message: str) -> str:
    """Sends an SMS instruction/message to the delivery partner."""
    try:
        response = requests.post(f"{ORDER_SERVICE_URL}/order/{order_id}/driver/contact", json={"instruction": message})
        if response.status_code == 200:
            return str(response.json())
        return "Failed to contact driver."
    except Exception as e:
        return str(e)

@tool
def file_order_complaint(order_id: int, issue_details: str) -> str:
    """Files a complaint for an order (e.g., missing items, bad quality) and automatically processes a refund."""
    try:
        response = requests.post(f"{ORDER_SERVICE_URL}/order/{order_id}/complaint", json={"issue_description": issue_details})
        if response.status_code == 200:
            return str(response.json())
        return "Failed to file complaint."
    except Exception as e:
        return str(e)

def get_all_tools():
    return [
        send_otp,
        verify_otp,
        get_customer_details,
        get_orders,
        get_order_items,
        get_payment_details,
        cancel_order,
        update_subscription,
        update_order_address,
        get_wallet_balance,
        check_refund_status,
        track_driver,
        contact_delivery_partner,
        file_order_complaint
    ]
