from typing import Dict,  Any
from bonuspay.common import get_logger, _call_bonuspay_api, _get_current_timestemp, get_global_partner_id
from mcp.server.fastmcp import Context

file_logger = get_logger()

def explain_topup_tools() -> str:
    """
    Explanation of BonusPay Topup (Deposit) Related Tools and Use Cases.
    """
    return """
    BonusPay Topup related tools include:
    - `get_deposit_address(customer_id, asset_code, network, language)`:
      Used to obtain a cryptocurrency deposit address for a customer. Used when a user needs to top up their BonusPay account, or when you need to generate an address to receive funds.
      For example: User asks "What is my ETH deposit address?" or "Please generate a USDT deposit address for customer M123."

    - `query_customer_deposit_order_page(start_time, end_time, start_index, size, language)`:
      Used for paginated queries of deposit order records within a specific time range. Used when a user wants to view past deposit history, or when an audit of deposit activity over a period is required.
      For example: User asks "How much did I deposit last week?" or "Please list the deposit records for the past month."

    - `get_customer_deposit_order(order_no, language)`:
      Used to query detailed information for a single deposit order based on its order number. Used when a user provides a specific order number and wants to know the status or details of that order.
      For example: User asks "What is the status of my order 20240701001?"
    """

async def get_deposit_address(
    ctx: Context,
    customer_id: str,
    asset_code: str,
    network: str,
    language: str = "en"
) -> str:
    """
    BonusPay API Call: [Get Deposit Account Address]
    Description: Merchants use their own identifiers to create cryptocurrency deposit addresses. This deposit address can receive blockchain transfers.
    @param customer_id: The unique identifier for the customer.
    @param asset_code: Asset code, e.g., 'ETH' or 'USDT'.
    @param network: The network to be used, e.g., 'ETH' or 'TRON'.
    @param language: The requested language (default: en).
    @return: Address information for making deposits.
    """
    api_path = "ccdeposit/getAddress"
    request_time = _get_current_timestemp()
    biz_content = {
        "customerId": customer_id,
        "assetCode": asset_code,
        "network": network
    }
    return await _call_bonuspay_api(
        ctx=ctx,
        api_path=api_path,
        biz_content=biz_content,
        request_time=request_time,
        language=language
    )

async def query_customer_deposit_order_page(
    ctx: Context,
    start_time: int,
    end_time: int,
    start_index: int,
    size: int,
    language: str = "en"
) -> str:
    """
    BonusPay API Call: [Paginated Query of Deposit Order Details]
    Description: Merchants use their own identifiers to query a paginated list of matching deposit orders.
    @param start_time: Queries deposit orders after this time.
    @param end_time: Queries deposit orders before this time.
    @param start_index: Page number (represents which page, 0 means the first page).
    @param size: Page size (represents the number of deposit order details per page).
    @param language: The requested language (default: en).
    @return: A detailed list of deposit top-up orders.
    """
    api_path = "ccdeposit/queryCustomerDepositOrderPage"
    request_time = _get_current_timestemp()
    biz_content = {
        "startTime": start_time,
        "endTime": end_time,
        "pageParam": {
            "number": start_index,
            "size": size
        }
    }
    return await _call_bonuspay_api(
        ctx=ctx,
        api_path=api_path,
        biz_content=biz_content,
        request_time=request_time,
        language=language
    )
    
async def get_customer_deposit_order(
    ctx: Context,
    order_no: str,
    language: str = "en"
) -> str:
    """
    BonusPay API Call: [Query Deposit Order Details by Deposit Order Number]
    Description: Merchants use their own deposit order number to query deposit order details.
    @param orderNo: BonusPay's deposit order number.
    @param language: The requested language (default: en).
    @return: Details of the deposit top-up order.
    """
    api_path = "ccdeposit/getCustomerDepositOrder"
    request_time = _get_current_timestemp()
    biz_content = {
        "orderNo": order_no
    }
    return await _call_bonuspay_api(
        ctx=ctx,
        api_path=api_path,
        biz_content=biz_content,
        request_time=request_time,
        language=language
    )

def add_topup_prompts(app_instance):
    app_instance.prompt()(explain_topup_tools)

def add_topup_tools(app_instance):
    app_instance.tool()(get_deposit_address)
    app_instance.tool()(query_customer_deposit_order_page) 
    app_instance.tool()(get_customer_deposit_order)