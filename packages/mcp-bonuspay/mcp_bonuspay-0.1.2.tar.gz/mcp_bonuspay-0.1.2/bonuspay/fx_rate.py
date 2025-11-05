from typing import Dict,  Any
from bonuspay.common import get_logger,  _call_bonuspay_api, get_global_partner_id, _get_current_timestemp
from mcp.server.fastmcp import Context

file_logger = get_logger()


def explain_fx_rate_tools() -> str:
    """
    BonusPay Payments (FX Rate) related tools and use cases.
    """
    return """
    BonusPay FX Rate related tools include:
    - `get_fx_rate(currency_pair, direction, language)`:
      Queries the real-time exchange rate between cryptocurrency and fiat currency. Used when the user wants to know the real-time buy/sell price for a specific currency pair.
      For example: The user asks "What is the buy exchange rate for USDT to INR?"
      Note: The provided exchange rate is for reference only, and the actual transaction rate may vary.  
    """

async def get_fx_rate(
    ctx: Context,
    currency_pair: str,
    direction: str,
    language: str = "en"
) -> str:
    """
    BonusPay API Call: [Query real-time exchange rates for cryptocurrency and fiat currency]
    Description: The provided exchange rate is for reference only; the actual exchange rate within a transaction order may vary due to differences between the query time and the order execution time.
    @param currency_pair: The trading pair identifier for cryptocurrency and fiat currency (separated by an underscore, e.g., USDT_INR).
    @param direction: Identifies whether it's a buy or sell, e.g., BUY and SELL.
    @param language: The requested language (default: en).
    @return: Details of the real-time exchange rate.
    """
    api_path = "fxrate/getFxrate"
    request_time = _get_current_timestemp()
    biz_content = {
        "currencyPair": currency_pair,
        "direction": direction
    }

    return await _call_bonuspay_api(
        ctx=ctx, 
        api_path=api_path, 
        biz_content=biz_content, 
        request_time=request_time, 
        language=language
    )

def add_fx_rate_prompts(app_instance):
    app_instance.prompt()(explain_fx_rate_tools)

def add_fx_rate_tools(app_instance):
    app_instance.tool()(get_fx_rate)