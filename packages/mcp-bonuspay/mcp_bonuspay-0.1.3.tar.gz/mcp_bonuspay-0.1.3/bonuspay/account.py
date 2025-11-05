from typing import Dict,  Any
from bonuspay.common import get_logger,  _call_bonuspay_api, get_global_partner_id, _get_current_timestemp
from mcp.server.fastmcp import Context

file_logger = get_logger()


def explain_account_tools() -> str:
    """
    Tools and use cases related to BonusPay payments (account-based).
    """
    return """
    BonusPay Account (Account) related tools include:
    - `get_account_list(asset_code_list, language)`:
      View the account list and balance for specified asset codes. Used when the user wants to understand their asset holdings.
      For example: The user asks "What are my ETH and USDT balances?"  
    """

async def get_account_list(
    ctx: Context,
    asset_code_list: list[str],
    language: str = "en"
) -> str:
    """
    BonusPay API Call: [Get Account List]
    Description: View account list and balance.
    @param asset_code_list: The list of asset codes to be queried, e.g., ['ETH', 'USDT'].
    @param language: The requested language (default: en).
    @return: Details of the account list.
    """
    api_path = "account/getAccountList"
    request_time = _get_current_timestemp()
    biz_content = {
        "assetCodeList": asset_code_list
    }

    return await _call_bonuspay_api(
        ctx=ctx, 
        api_path=api_path, 
        biz_content=biz_content, 
        request_time=request_time, 
        language=language
    )

def add_account_prompts(app_instance):
    app_instance.prompt()(explain_account_tools)

def add_account_tools(app_instance):
    app_instance.tool()(get_account_list)