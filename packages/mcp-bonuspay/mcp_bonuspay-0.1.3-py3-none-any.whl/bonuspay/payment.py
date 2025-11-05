from typing import Dict,  Any
from bonuspay.common import get_logger,  _call_bonuspay_api, get_global_partner_id, _get_current_timestemp
from mcp.server.fastmcp import Context

file_logger = get_logger()


def explain_payment_tools() -> str:
    """
    BonusPay Payments (Payment) related tools and use cases.
    """
    return """
    BonusPay Payment related tools include:
    - `acquire_order(merchant_order_no, subject, pay_scene_code, total_amount, reference_amount, pay_scene_params, accessory_content, reserved, notify_url, payee_mid, language)`:
      Creates a new payment order to receive cryptocurrency transfers. Used when a user wants to purchase goods/services, and you need to initiate a payment process.
      For example: User says "I want to buy an iPad, order number M123, amount 100 USDT, please help me create the order."
     - `cancel_order(merchant_order_no, order_no, language)`:
      Cancels orders that have been created but not yet paid. Used to handle situations like payment failure, user timeout, or to prevent duplicate payments.
      For example: User says "My order M123 failed payment, please cancel it."
    - `accept_order(merchant_order_no, order_no, language)`:
      Accepts orders with an underpaid or overpaid status. Used to handle abnormal payment situations where the merchant decides to accept partial payment or overpayment.
      For example: User asks "The payment amount for order M123 is incorrect, can it be accepted?"
    - `get_order(merchant_order_no, order_no, language)`:
      Queries the detailed status of a payment order based on the order number. Used when the user wants to know the order progress, or when you need to confirm the payment status for subsequent business processing.
      For example: User asks "What is the payment status of order M123?"
    - `get_payment_deposit_event_list(merchant_order_no, order_no, language)`:
      Queries top-up events for a payment order. Used after obtaining the top-up address to track the actual arrival of funds.
      For example: User asks "Have any top-up events occurred for order M123?"
    - `refund_order(refund_merchant_order_no, amount, chain_code, refund_address, origin_merchant_order_no, origin_order_no, operator_name, reason, reserved, notify_url, language)`:
      Creates a refund order to return funds to the buyer. Used to handle refund requests resulting from reasons on both the buyer's and seller's sides.
      For example: User says "I want to refund 10 USDT for order M123."
    - `get_refund_order(refund_merchant_order_no, order_no, language)`:
      Queries the detailed status of a refund order. Used to track the refund process or troubleshoot refund anomalies.
      For example: User asks "What is the status of my refund order R456?" 
    """

async def acquire_order(
    ctx: Context,
    merchant_order_no: str, 
    subject: str, 
    pay_scene_code: str, 
    total_amount: Dict[str,  Any] | None = None,  
    reference_amount: Dict[str,  Any] | None = None,  
    pay_scene_params: Dict[str,  Any] | None = None,  
    accessory_content: Dict[str,  Any] | None = None,  
    reserved: str | None = None,  
    notify_url: str | None = None,  
    payee_mid: str | None = None,  
    language: str = "en"
) -> str:
    """
    BonusPay API Call: [Create Payment Order]
    Description: Submits a payment order request to return a wallet address for receiving transfers. This is an idempotent API.
    @param merchant_order_no: Merchant's payment order number.
    @param subject: Name of the product purchased.
    @param pay_scene_code: Payment scene code, e.g., 'API', 'CHECK_OUT', 'PLATON_QRPAY'.
    @param total_amount (Optional): Cryptocurrency amount information required for the order payment (either `total_amount` or `reference_amount` must be provided).
                        E.g.: {"currency": "ETH", "amount": 1.01}
                        @param currency: Cryptocurrency identifier.
                        @param amount: Required cryptocurrency amount.
    @param reference_amount (Optional): Fiat currency amount information required for the order payment (either `total_amount` or `reference_amount` must be provided).
                        E.g.: {"exchangeCurrencyCode": "USDT",  "refAmount": {"currency": "INR", "amount": 1.01}}
                        @param exchangeCurrencyCode: Identifier of the target cryptocurrency to convert the fiat currency to.
                        @param currency: Fiat currency identifier.
                        @param amount: Required fiat currency amount.
    @param pay_scene_params (Optional): Payment scene parameters, influenced by the `pay_scene_code` parameter.
                        When `pay_scene_code` = 'API', it is: {"chainCode": "ETH", "payChannelCode": "CHAIN", "payerEmail": "meiya...@gmail.com"}
                                            @chainCode: Blockchain code used for payment, e.g.: 'TRON', 'POLYGON', 'ETH', 'BTC'.
                                            @payChannelCode: Merchant-specified payment channel code, e.g.: 'CHAIN'.
                                            @payerEmail (Optional): Payer's email.
                        When `pay_scene_code` = 'CHECK_OUT', it is: {"redirectUrl":"http://www.yoursite.com/web/paydone.html?orderId=414768633924763654"}
                                            @redirectUrl (Optional): Merchant-provided website URL. After the order payment is successful, the user will be redirected to this address.
                        When `pay_scene_code` = 'PLATON_QRPAY', this field should not exist.
    @param accessory_content (Optional): Additional information about the order, such as order description or product images. {"amountDetail": {...}, "goodsDetail": {...}, "terminalDetail": {...}}
                        @amountDetail (Optional): Amount details.
                        @goodsDetail (Optional): Goods details.
                        @terminalDetail (Optional): Terminal details.
    @param reserved (Optional): Reserved field, if provided, please pass it as a **double-quoted string**, e.g.: "order desc".
    @param notify_url (Optional): Backend notification URL, if provided, please pass it as a **double-quoted string**, e.g.: "http://...".
    @param payee_mid (Optional): Payee member's merchant ID. Default "" means the merchant itself. If provided, please pass it as a **double-quoted string**, e.g.: "200000345276".
    @param language: Requested language (default: en).
    @return: Order information awaiting payment.
    """
    api_path = "crypto/placeOrder"
    request_time = _get_current_timestemp()
    expired_time = request_time + 6 * 60 * 1000 # + 6 min
    biz_content = {
        "expiredTime": expired_time,
        "merchantOrderNo": merchant_order_no,
        "subject": subject,
        "paySceneCode": pay_scene_code
    }
    if total_amount is not None:
        biz_content["totalAmount"] = total_amount
    if reference_amount is not None:
        biz_content["refAmount"] = reference_amount
    if pay_scene_params is not None:
        biz_content["paySceneParams"] = pay_scene_params
    if accessory_content is not None:
        biz_content["accessoryContent"] = accessory_content
    if reserved is not None:
        biz_content["reserved"] = reserved
    if notify_url is not None:
        biz_content["notifyUrl"] = notify_url
    if payee_mid is not None:
        biz_content["payeeMid"] = payee_mid

    return await _call_bonuspay_api(
        ctx=ctx, 
        api_path=api_path, 
        biz_content=biz_content, 
        request_time=request_time, 
        language=language
    )

async def cancel_order(
    ctx: Context,
    merchant_order_no: str | None = None,  
    order_no: str | None = None,  
    language: str = "en"
) -> str:
    """
    BonusPay API Call: [Cancel Payment Order]
    Description: If a merchant's order payment fails and a new order number is generated for re-payment, the original order number should be cancelled to prevent duplicate payments;
        after the system creates an order, if the user payment times out and the system stops processing, please call the order cancellation interface to prevent the user from attempting further payments.
    @param merchant_order_no (Optional): Merchant's payment order number. If provided, please pass it as a **double-quoted string**, e.g.: "P200000444476" (either this or `order_no` must be provided).
    @param order_no (Optional): BonusPay payment order number. If provided, please pass it as a **double-quoted string**, e.g.: "21111111116" (either this or `merchant_order_no` must be provided).
    @param language: Requested language (default: en).
    @return: Result information indicating whether the request was successful or failed.
    """
    api_path = "crypto/cancelOrder"
    request_time = _get_current_timestemp()
    biz_content = {}
    if merchant_order_no is not None:
        biz_content["merchantOrderNo"] = merchant_order_no
    if order_no is not None:
        biz_content["orderNo"] = order_no
        
    return await _call_bonuspay_api(
        ctx=ctx, 
        api_path=api_path, 
        biz_content=biz_content, 
        request_time=request_time, 
        language=language
    )

async def accept_order(
    ctx: Context,
    merchant_order_no: str | None = None,  
    order_no: str | None = None,  
    language: str = "en"
) -> str:
    """
    BonusPay API Call: [Accept Payment Order]
    Description: When an order is in an underpaid or overpaid status, the merchant can accept the order through this interface.
    @param merchant_order_no (Optional): Merchant's payment order number. If provided, please pass it as a **double-quoted string**, e.g.: "P200000444476" (either this or `order_no` must be provided).
    @param order_no (Optional): BonusPay payment order number. If provided, please pass it as a **double-quoted string**, e.g.: "21111111116" (either this or `merchant_order_no` must be provided).
    @param language: Requested language (default: en).
    @return: Result information indicating whether the request was successful or failed.
    """
    api_path = "crypto/acceptOrder"
    request_time = _get_current_timestemp()
    biz_content = {}
    if merchant_order_no is not None:
        biz_content["merchantOrderNo"] = merchant_order_no
    if order_no is not None:
        biz_content["orderNo"] = order_no

    return await _call_bonuspay_api(
        ctx=ctx, 
        api_path=api_path, 
        biz_content=biz_content, 
        request_time=request_time, 
        language=language
    )

async def get_order(
    ctx: Context,
    merchant_order_no: str | None = None,  
    order_no: str | None = None,  
    language: str = "en"
) -> str:
    """
    BonusPay API Call: [Query Payment Order Details by Merchant's Payment Order Number or BonusPay Payment Order Number]
    Description: Merchants can complete subsequent business logic by querying the order status.
        Situations requiring the query interface call include:
            1. When there are abnormal conditions such as merchant backend, network, server issues, and the merchant system ultimately does not receive payment notifications.
            2. When calling the payment interface, a system error occurs or the transaction status is unknown.
            3. Before calling the Cancel Order API, it is necessary to confirm the payment status.
    @param merchant_order_no (Optional): Merchant's payment order number. If provided, please pass it as a **double-quoted string**, e.g.: "P200000444476" (either this or `order_no` must be provided).
    @param order_no (Optional): BonusPay payment order number. If provided, please pass it as a **double-quoted string**, e.g.: "21111111116" (either this or `merchant_order_no` must be provided).
    @param language: Requested language (default: en).
    @return: Details of the payment order.
    """
    api_path = "crypto/getOrder"
    request_time = _get_current_timestemp()
    biz_content = {}
    if merchant_order_no is not None:
        biz_content["merchantOrderNo"] = merchant_order_no
    if order_no is not None:
        biz_content["orderNo"] = order_no

    return await _call_bonuspay_api(
        ctx=ctx, 
        api_path=api_path, 
        biz_content=biz_content, 
        request_time=request_time, 
        language=language
    )

async def get_payment_deposit_event_list(
    ctx: Context,
    merchant_order_no: str | None = None,  
    order_no: str | None = None,  
    language: str = "en"
) -> str:
    """
    BonusPay API Call: [Query Payment Deposit Events by Merchant's Payment Order Number or BonusPay Payment Order Number]
    Description: After obtaining the top-up address, merchants can query deposit events by calling this API.
    @param merchant_order_no (Optional): Merchant's payment order number. If provided, please pass it as a **double-quoted string**, e.g.: "P200000444476" (either this or `order_no` must be provided).
    @param order_no (Optional): BonusPay payment order number. If provided, please pass it as a **double-quoted string**, e.g.: "21111111116" (either this or `merchant_order_no` must be provided).
    @param language: Requested language (default: en).
    @return: Details of the payment deposit events for the payment order.
    """
    api_path = "crypto/getPaymentDepositEventList"
    request_time = _get_current_timestemp()
    biz_content = {}
    if merchant_order_no is not None:
        biz_content["merchantOrderNo"] = merchant_order_no
    if order_no is not None:
        biz_content["orderNo"] = order_no
        
    return await _call_bonuspay_api(
        ctx=ctx, 
        api_path=api_path, 
        biz_content=biz_content, 
        request_time=request_time, 
        language=language
    )

async def refund_order(
    ctx: Context,
    refund_merchant_order_no: str, 
    amount: Dict[str,  Any],
    chain_code: str,
    refund_address: str,
    origin_merchant_order_no: str | None = None,  
    origin_order_no: str | None = None,  
    operator_name: str| None = None,  
    reason: str| None = None,  
    reserved: str| None = None,  
    notify_url: str | None = None,  
    language: str = "en"
) -> str:
    """
    BonusPay API Call: [Create Refund Order by Merchant's Refund Order Number and Corresponding Merchant's Payment Order Number or Corresponding BonusPay Payment Order Number]
    Description: When a refund is required for reasons from either the buyer or seller after an order has been created for some time, the seller can initiate the return of funds to the buyer.
        Upon receiving and verifying the refund request, BonusPay will initiate a refund to the refund address according to refund rules and will charge additional refund fees.
    @param refund_merchant_order_no: Merchant's refund order number.
    @param amount: Details of the refund amount.
                        @param currency: Cryptocurrency identifier.
                        @param amount: Required cryptocurrency amount.
    @param chain_code: Blockchain code used for the refund, e.g.: 'TRON', 'POLYGON', 'ETH', 'BTC'.
    @param refund_address: Account address to receive the refund amount.
    @param origin_merchant_order_no (Optional): Merchant's payment order number. If provided, please pass it as a **double-quoted string**, e.g.: "P200000444476" (either this or `origin_order_no` must be provided).
    @param origin_order_no (Optional): BonusPay payment order number. If provided, please pass it as a **double-quoted string**, e.g.: "21111111116" (either this or `origin_merchant_order_no` must be provided).
    @param operator_name (Optional): Refund operator's name. If provided, please pass it as a **double-quoted string**, e.g.: "gavin".
    @param reason (Optional): Reason for refund. If provided, please pass it as a **double-quoted string**, e.g.: "user refund only".
    @param reserved (Optional): Reserved field. If provided, please pass it as a **double-quoted string**, e.g.: "order desc".
    @param notify_url (Optional): Backend notification URL. If provided, please pass it as a **double-quoted string**, e.g.: "https://...".
    @param language: Requested language (default: en).
    @return: Details of the refund order.
    """
    api_path = "crypto/refund/placeOrder"
    request_time = _get_current_timestemp()
    biz_content = {
        "refundMerchantOrderNo": refund_merchant_order_no,
        "amount": amount,
        "chainCode": chain_code,
        "refundAddress": refund_address
    }

    if origin_merchant_order_no is not None:
        biz_content["originMerchantOrderNo"] = origin_merchant_order_no
    if origin_order_no is not None:
        biz_content["originOrderNo"] = origin_order_no
    if operator_name is not None:
        biz_content["operatorName"] = operator_name
    if reason is not None:
        biz_content["reason"] = reason
    if reserved is not None:
        biz_content["reserved"] = reserved
    if notify_url is not None:
        biz_content["notifyUrl"] = notify_url

    return await _call_bonuspay_api(
        ctx=ctx, 
        api_path=api_path,  
        biz_content=biz_content, 
        request_time=request_time, 
        language=language
    )

async def get_refund_order(
    ctx: Context,
    refund_merchant_order_no: str | None = None,  
    order_no: str | None = None,  
    language: str = "en"
) -> str:
    """
    BonusPay API Call: [Query Refund Order Details by Merchant's Refund Order Number or BonusPay Refund Order Number]
    Description: Merchants can actively query the order status through the query order interface to complete subsequent business logic.
        Situations requiring the query interface call include:
            1. When there are abnormal conditions such as merchant backend, network, server issues, and the merchant system ultimately does not receive refund notifications.
            2. When calling the refund interface, a system error occurs or the transaction status is unknown.
    @param refund_merchant_order_no (Optional): Merchant's refund order number. If provided, please pass it as a **double-quoted string**, e.g.: "R200000444476" (either this or `order_no` must be provided).
    @param order_no (Optional): BonusPay refund order number. If provided, please pass it as a **double-quoted string**, e.g.: "31111111116" (either this or `refund_merchant_order_no` must be provided).
    @param language: Requested language (default: en).
    @return: Details of the refund order.
    """
    api_path = "crypto/refund/getOrder"
    request_time = _get_current_timestemp()
    biz_content = {}
    if refund_merchant_order_no is not None:
        biz_content["refundMerchantOrderNo"] = refund_merchant_order_no
    if order_no is not None:
        biz_content["orderNo"] = order_no

    return await _call_bonuspay_api(
        ctx=ctx, 
        api_path=api_path, 
        biz_content=biz_content, 
        request_time=request_time, 
        language=language
    )

def add_payment_prompts(app_instance):
    app_instance.prompt()(explain_payment_tools)

def add_payment_tools(app_instance):
    app_instance.tool()(acquire_order)
    app_instance.tool()(cancel_order)
    app_instance.tool()(accept_order)
    app_instance.tool()(get_order)
    app_instance.tool()(get_payment_deposit_event_list)
    app_instance.tool()(refund_order)
    app_instance.tool()(get_refund_order)