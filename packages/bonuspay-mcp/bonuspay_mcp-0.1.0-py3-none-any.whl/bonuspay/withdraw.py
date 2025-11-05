from typing import Dict,  Any
from bonuspay.common import get_logger,  _call_bonuspay_api, get_global_partner_id, _get_current_timestemp
from mcp.server.fastmcp import Context

file_logger = get_logger()

def explain_withdraw_tools() -> str:
    """
    BonusPay Payments (Withdraw/Transfer) related tools and use cases.
    """
    return """
    BonusPay Withdrawal (Withdraw/Transfer) related tools include:
    - `withdraw_order(address, network, merchant_order_no, expected_received_amount, reference_amount, notify_url, language)`:
      Creates a withdrawal order to withdraw merchant assets to a specified address (requires the receiving address to be in the order book). Used when you need to withdraw funds to a preset or linked address.
      For example: User says "I want to withdraw ETH to address X."
    - `transfer_order(address, network, merchant_order_no, expected_received_amount, reference_amount, notify_url, language)`:
      Creates a transfer order to transfer merchant assets to any address. Used when you need to transfer funds to any non-preset external address.
      For example: User says "Please transfer 50 USDT to address Y."
    - `get_withdraw_order(merchant_order_no, order_no, language)`:
      Queries the detailed status of a withdrawal order. Used for tracking withdrawal processes or troubleshooting withdrawal anomalies.
      For example: User asks "What is the status of withdrawal order W123?"
    - `get_withdraw_networks(asset_code, language)`:
      Queries the withdrawal networks supported by a cryptocurrency based on the asset code. Used when the user wants to know which withdrawal networks a certain coin supports.
      For example: User asks "Which withdrawal networks does USDT support?"
    """

async def withdraw_order(
    ctx: Context,
    address: str,
    network: str,
    merchant_order_no: str,
    expected_received_amount: Dict[str,  Any] | None = None,  
    reference_amount: Dict[str,  Any] | None = None,  
    notify_url: str | None = None,  
    language: str = "en"
) -> str:
    """
    BonusPay API Call: [Create Withdrawal Order]
    Description: Submits a withdrawal order request to withdraw merchant assets (requires the receiving address to be in the order book).
    @param address: The account address to receive the withdrawal.
    @param network: The blockchain code used by the receiving account address, e.g.: 'TRON', 'POLYGON', 'ETH', 'BTC'.
    @param merchant_order_no: Merchant's withdrawal order number.
    @param expected_received_amount (Optional): Cryptocurrency amount information required for the order withdrawal (either `expected_received_amount` or `reference_amount` must be provided).
                        E.g.: {"currency": "ETH", "amount": 1.01}
                        @param currency: Cryptocurrency identifier.
                        @param amount: Required cryptocurrency amount.
    @param reference_amount (Optional): Fiat currency amount information required for the order withdrawal (either `expected_received_amount` or `reference_amount` must be provided).
                        E.g.: {"exchangeCurrencyCode": "USDT",  "refAmount": {"currency": "INR", "amount": 1.01}}
                        @param exchangeCurrencyCode: Identifier of the target cryptocurrency to convert the fiat currency to.
                        @param currency: Fiat currency identifier.
                        @param amount: Required fiat currency amount.
    @param notify_url (Optional): Backend notification URL. If provided, please pass it as a **double-quoted string**, e.g.: "https://...".
    @param language: Requested language (default: en).
    @return: Withdrawal order information.
    """
    api_path = "ccwithdraw/placeOrder"
    request_time = _get_current_timestemp()
    biz_content = {
        "address": address,
        "network": network,
        "merchantOrderNo": merchant_order_no
    }
    if expected_received_amount is not None:
        biz_content["expectedReceivedAmount"] = expected_received_amount
    if reference_amount is not None:
        biz_content["refAmount"] = reference_amount
    if notify_url is not None:
        biz_content["notifyUrl"] = notify_url

    return await _call_bonuspay_api(
        ctx=ctx, 
        api_path=api_path, 
        biz_content=biz_content, 
        request_time=request_time, 
        language=language
    )

async def transfer_order(
    ctx: Context,
    address: str,
    network: str,
    merchant_order_no: str,
    expected_received_amount: Dict[str,  Any] | None = None,  
    reference_amount: Dict[str,  Any] | None = None,  
    notify_url: str | None = None,  
    language: str = "en"
) -> str:
    """
    BonusPay API Call: [Create Transfer Order]
    Description: Submits a transfer order request to move merchant assets (the receiving address can be any address).
    @param address: The account address to receive the transfer.
    @param network: The blockchain code used by the receiving account address, e.g.: 'TRON', 'POLYGON', 'ETH', 'BTC'.
    @param merchant_order_no: Merchant's transfer order number.
    @param expected_received_amount (Optional): Cryptocurrency amount information required for the order transfer (either `expected_received_amount` or `reference_amount` must be provided).
                        E.g.: {"currency": "ETH", "amount": 1.01}
                        @param currency: Cryptocurrency identifier.
                        @param amount: Required cryptocurrency amount.
    @param reference_amount (Optional): Fiat currency amount information required for the order transfer (either `expected_received_amount` or `reference_amount` must be provided).
                        E.g.: {"exchangeCurrencyCode": "USDT",  "refAmount": {"currency": "INR", "amount": 1.01}}
                        @param exchangeCurrencyCode: Identifier of the target cryptocurrency to convert the fiat currency to.
                        @param currency: Fiat currency identifier.
                        @param amount: Required fiat currency amount.
    @param notify_url (Optional): Backend notification URL. If provided, please pass it as a **double-quoted string**, e.g.: "https://...".
    @param language: Requested language (default: en).
    @return: Transfer order information.
    """
    api_path = "ccwithdraw/transfer"
    request_time = _get_current_timestemp()
    biz_content = {
        "address": address,
        "network": network,
        "merchantOrderNo": merchant_order_no
    }
    if expected_received_amount is not None:
        biz_content["expectedReceivedAmount"] = expected_received_amount
    if reference_amount is not None:
        biz_content["refAmount"] = reference_amount
    if notify_url is not None:
        biz_content["notifyUrl"] = notify_url

    return await _call_bonuspay_api(
        ctx=ctx, 
        api_path=api_path, 
        biz_content=biz_content, 
        request_time=request_time, 
        language=language
    )

async def get_withdraw_order(
    ctx: Context,
    merchant_order_no: str | None = None,  
    order_no: str | None = None,  
    language: str = "en"
) -> str:
    """
    BonusPay API Call: [Query Withdrawal or Transfer Order Details by Merchant's Withdrawal or Transfer Order Number]
    Description: Merchants can complete subsequent business logic by querying the order status.
        Situations requiring the query interface call include:
            1. When there are abnormal conditions such as merchant backend, network, server issues, and the merchant system ultimately does not receive withdrawal or transfer notifications.
            2. When calling the withdrawal or transfer interface, a system error occurs or the transaction status is unknown.
    @param merchant_order_no (Optional): Merchant's withdrawal or transfer order number. If provided, please pass it as a **double-quoted string**, e.g.: "W2000005555566" (either this or `order_no` must be provided).
    @param order_no (Optional): BonusPay withdrawal or transfer order number. If provided, please pass it as a **double-quoted string**, e.g.: "4000005555566" (either this or `merchant_order_no` must be provided).
    @param language: Requested language (default: en).
    @return: Details of the withdrawal or transfer order.
    """
    api_path = "ccwithdraw/getOrder"
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

async def get_withdraw_networks(
    ctx: Context,
    asset_code: str,
    language: str = "en"
) -> str:
    """
    BonusPay API Call: [Query Supported Withdrawal Network Information for a Cryptocurrency in Withdrawal Orders by Asset (Cryptocurrency) Code]
    Description: After obtaining the top-up address, merchants can query deposit events by calling this API.
    @param asset_code: Asset code, e.g., 'ETH' or 'USDT'.
    @param language: Requested language (default: en).
    @return: Supported withdrawal network information for the asset (cryptocurrency).
    """
    api_path = "ccwithdraw/getNetworks"
    request_time = _get_current_timestemp()
    biz_content = {
        "assetCode": asset_code
    }

    return await _call_bonuspay_api(
        ctx=ctx, 
        api_path=api_path,  
        biz_content=biz_content, 
        request_time=request_time, 
        language=language
    )

def add_withdraw_prompts(app_instance):
    app_instance.prompt()(explain_withdraw_tools)

def add_withdraw_tools(app_instance):
    app_instance.tool()(withdraw_order)
    app_instance.tool()(transfer_order)
    app_instance.tool()(get_withdraw_order)
    app_instance.tool()(get_withdraw_networks)