import os
from mcp.server import FastMCP
from bonuspay.common import TEST_API_BASE_URL, MAIN_API_BASE_URL
from bonuspay.common import set_api_base_url, get_api_base_url
from bonuspay.common import get_logger, add_overview_prompt
from bonuspay.common import set_global_private_key_path, set_global_public_key_path
from bonuspay.common import set_global_partner_id
from bonuspay.topup import add_topup_tools, add_topup_prompts
from bonuspay.payment import add_payment_tools, add_payment_prompts
from bonuspay.withdraw import add_withdraw_tools, add_withdraw_prompts
from bonuspay.fx_rate import add_fx_rate_tools, add_fx_rate_prompts
from bonuspay.account import add_account_tools, add_account_prompts
from bonuspay import __version__

logger = get_logger()

app = FastMCP("BonusPay API")

# prompts
add_overview_prompt(app)
add_topup_prompts(app)
add_payment_prompts(app)
add_withdraw_prompts(app)
add_fx_rate_prompts(app)
add_account_prompts(app)

# tools
add_topup_tools(app)
add_payment_tools(app)
add_withdraw_tools(app)
add_fx_rate_tools(app)
add_account_tools(app)

def _initialize_server_config(host: str, port: int, network: str, private_key_path: str, public_key_path: str, partner_id: str):
    # check network
    if network == "test":
        base_url = TEST_API_BASE_URL
    elif network == "main":
        base_url = MAIN_API_BASE_URL
    else:
        # In fact, we won't get here because argparse has choices validation.
        logger.error(f"Invalid network specified: {network}")
        base_url = TEST_API_BASE_URL
    set_api_base_url(base_url)

    # private_key_path
    if not private_key_path:
        logger.error("Not find private-key path. ", exc_info=True)
        exit(1)
    if not os.path.exists(private_key_path):
        logger.error(f"Not exist private-key file: '{private_key_path}'. ")
        exit(1)
    set_global_private_key_path(private_key_path)
    logger.info(f"Ready private-key file: '{private_key_path}'. ")

    # public_key_path
    if not public_key_path:
        logger.error("Not find public-key path. ", exc_info=True)
        exit(1)
    if not os.path.exists(public_key_path):
        logger.error(f"Not exist public-key file: '{public_key_path}'. ")
        exit(1)
    set_global_public_key_path(public_key_path)
    logger.info(f"Ready public-key file: '{public_key_path}'. ")

    # partner id
    if not partner_id:
        logger.error("Must set partner id. ", exc_info=True)
        exit(1)
    set_global_partner_id(partner_id)
    logger.info(f"Ready partner id: '{partner_id}'. ")

    # set host and port for app
    app.settings.host = host
    app.settings.port = port


def run_sse(host: str, port: int, network: str, private_key_path: str, public_key_path: str, partner_id: str):
    """Run BonusPay API MCP Server in SSE mode."""
    _initialize_server_config(host, port, network, private_key_path, public_key_path, partner_id)
    try:
        logger.info(f"Starting BonusPay API MCP Server: {__version__} for {network} network with sse transport on {host}:{port}. API Base URL: {get_api_base_url()}")
        app.run(transport="sse")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed: {e}", exc_info=True)
        raise
    finally:
        logger.info("Server shutdown complete")     

def run_streamable_http(host: str, port: int, network: str, private_key_path: str, public_key_path: str, partner_id: str):
    """Run BonusPay API MCP Server in streamable HTTP mode."""
    _initialize_server_config(host, port, network, private_key_path, public_key_path, partner_id)
    try:
        logger.info(f"Starting BonusPay API MCP Server: {__version__} for {network} network with streamable HTTP transport on {host}:{port}. API Base URL: {get_api_base_url()}")
        app.run(transport="streamable-http")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed: {e}", exc_info=True)
        raise
    finally:
        logger.info("Server shutdown complete")              

def run_stdio(network: str, private_key_path: str, public_key_path: str, partner_id: str):
    """Run BonusPay API MCP Server in stdio mode."""
    _initialize_server_config("", "", network, private_key_path, public_key_path, partner_id)
    try:
        logger.info(f"Starting BonusPay API MCP Server: {__version__} for {network} network with stdio transport. API Base URL: {get_api_base_url()}")
        app.run(transport="stdio")
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed: {e}", exc_info=True)
        raise
    finally:
        logger.info("Server shutdown complete")  