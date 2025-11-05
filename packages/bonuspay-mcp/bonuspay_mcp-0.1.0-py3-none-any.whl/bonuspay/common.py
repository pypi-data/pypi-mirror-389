import logging
import os
import time
import httpx
import json
import base64
from typing import Dict, Any, Optional
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
from dotenv import load_dotenv
from mcp.server.fastmcp import Context


# --- log setting---
logger = logging.getLogger(__name__)

if not logger.handlers:
    logger.setLevel(logging.INFO)
    PROJECT_ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOG_FILE_PATH = os.path.join(PROJECT_ROOT_DIR, 'bonuspay_server.log')
    file_handler = logging.FileHandler(LOG_FILE_PATH)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

load_dotenv()
# base api url
_API_BASE_URL: str = ""
TEST_API_BASE_URL : str = "http://api.testbonuspay.network/sgs/api/"
MAIN_API_BASE_URL : str = "https://api.bonuspay.network/sgs/api/"
def set_api_base_url(url: str):
    global _API_BASE_URL
    _API_BASE_URL = url
def get_api_base_url() -> str:
    if not _API_BASE_URL:
        logger.warning("API_BASE_URL has not been set. Defaulting to testnet API.")
        return TEST_API_BASE_URL
    return _API_BASE_URL
# private key path
_GLOBAL_PRIVATE_KEY_PATH: Optional[str] = None
def set_global_private_key_path(path: str):
    global _GLOBAL_PRIVATE_KEY_PATH
    _GLOBAL_PRIVATE_KEY_PATH = path
    logger.info(f"The globl private-key path is: {_GLOBAL_PRIVATE_KEY_PATH}")
def get_global_private_key_path() -> Optional[str]:
    return _GLOBAL_PRIVATE_KEY_PATH
# public key path
_GLOBAL_PUBLIC_KEY_PATH: Optional[str] = None
def set_global_public_key_path(path: str):
    global _GLOBAL_PUBLIC_KEY_PATH
    _GLOBAL_PUBLIC_KEY_PATH = path
    logger.info(f"The globl public-key path is: {_GLOBAL_PUBLIC_KEY_PATH}")
def get_global_public_key_path() -> Optional[str]:
    return _GLOBAL_PUBLIC_KEY_PATH
# partner id
_GLOBAL_PARTNER_ID: Optional[str] = None
def set_global_partner_id(id: str):
    global _GLOBAL_PARTNER_ID
    _GLOBAL_PARTNER_ID = id
    logger.info(f"The globl partner id is: {_GLOBAL_PARTNER_ID}")
def get_global_partner_id() -> Optional[str]:
    return _GLOBAL_PARTNER_ID
# Helper Function: Private Key Loading from Bytes
def load_private_key_from_bytes(key_bytes: bytes):
    try:
        private_key = serialization.load_pem_private_key(
            key_bytes,
            password=None,  # If the private key is encrypted, please provide the password here (bytes type).
            backend=default_backend()
        )
        logger.info("Private key bytes loaded successfully. ")
        return private_key
    except ValueError as e:
        logger.error(f"Failed to load private key, please check file format: {e}")
        raise ValueError(f"Failed to load private key, please check file format: {e}")
    except Exception as e:
        logger.error(f"An unknown error occurred while loading the private key: {e}")
        raise Exception(f"An unknown error occurred while loading the private key: {e}")

# Helper Function: Private Key Loading from '.pem' File Path
def load_private_key_from_path(key_path: str):
    if not os.path.exists(key_path):
        logger.error(f"Private key file not found: {key_path}")
        raise FileNotFoundError(f"Private key file not found: {key_path}")
    try:
        with open(key_path, "rb") as key_file:
            private_key = serialization.load_pem_private_key(
                key_file.read(),
                password=None,
                backend=default_backend()
            )
        logger.info(f"Private key loaded successfully from {key_path}.")
        return private_key
    except ValueError as e:
        logger.error(f"Failed to load private key, please check file format: {e}")
        raise ValueError(f"Failed to load private key, please check file format: {e}")
    except Exception as e:
        logger.error(f"An unknown error occurred while loading the private key: {e}")
        raise Exception(f"An unknown error occurred while loading the private key: {e}")

# Helper Function: Serialize Public Key to PEM Format
def _serialize_public_key(public_key: RSAPublicKey) -> str:
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode('utf-8')
def _get_current_timestemp() -> int:
    return int(time.time() * 1000)

# # Helper Function: Public Key Loading from '.pem' File Path
def load_public_key_from_path(key_path: str) -> RSAPublicKey:
    if not os.path.exists(key_path):
        logger.error(f"Public key file not found: {key_path}")
        raise FileNotFoundError(f"Public key file not found: {key_path}")
    try:
        with open(key_path, "rb") as key_file:
            public_key = serialization.load_pem_public_key(
                key_file.read(),
                backend=default_backend()
            )
        logger.info(f"Public key loaded successfully from {key_path}. ")
        return public_key
    except ValueError as e:
        logger.error(f"Failed to load public key, please check file format: {e}")
        raise ValueError(f"Failed to load public key, please check file format: {e}")
    except Exception as e:
        logger.error(f"An unknown error occurred while loading the public key: {e}")
        raise Exception(f"An unknown error occurred while loading the public key: {e}")

def get_logger():
    return logger

async def generate_signature(
    ctx: Context,
    payload_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate a SHA256WithRSA signature for the JSON request body using the uploaded private key.
    @param payload_data: The complete JSON request body as a string (already containing `requestTime`), 
                        used as input for the signature.
    @return: The Base64-encoded SHA256WithRSA signature.
    """
    private_key_path = get_global_private_key_path()
    resp_json = {}
    if not private_key_path:
        error_msg = "Failed signature: private key file path not provided, ensure the 'BONUSPAY_PRIVATE_KEY_PATH' environment variable is set. "
        await ctx.error(error_msg)
        logger.error(error_msg, exc_info=True)
        resp_json["code"] = -1
        resp_json["errMsg"] = error_msg
        return resp_json
    private_key: Optional[RSAPrivateKey] = None
    try:
        private_key = load_private_key_from_path(private_key_path)
    except Exception as e:
        error_msg = f"Failed signature, Unable to load private key from path '{private_key_path}': {str(e)}"
        await ctx.error(error_msg)
        logger.error(error_msg, exc_info=True)
        resp_json["code"] = -1
        resp_json["errMsg"] = error_msg
        return resp_json

    if private_key is None:
        error_msg = "Failed signature, private key does not exist. "
        await ctx.error(error_msg)
        logger.error(error_msg, exc_info=True)
        resp_json["code"] = -1
        resp_json["errMsg"] = error_msg
        return resp_json


    try:
        # Reserializing to a compact string to ensure format consistency (BonusPay API signature requirement). 
        final_json_payload_str_for_signing = json.dumps(payload_data, separators=(',', ':'), ensure_ascii=False)
        encoded_message = final_json_payload_str_for_signing.encode('utf-8')

        signature_bytes = private_key.sign(
            encoded_message,
            padding.PKCS1v15(),
            hashes.SHA256()
        )

        base64_signature = base64.b64encode(signature_bytes).decode('utf-8')

        await ctx.debug(f"Successful signature, JSON string used for signing: {final_json_payload_str_for_signing}")
        logger.debug(f"Successful signature, JSON string used for signing: {final_json_payload_str_for_signing}")

        resp_json["code"] = 0
        resp_json["errMsg"] = "success"
        resp_json["data"] = base64_signature
        return resp_json
    except json.JSONDecodeError as e:
        errMsg = f"Failed signature, json_payload_str is not a valid JSON format: {e}"
        await ctx.error(errMsg)
        logger.error(errMsg, exc_info=True)
        resp_json["code"] = -1
        resp_json["errMsg"] = errMsg
        return resp_json
    except Exception as e:
        errMsg = f"Failed signature, An error occurred while generating the signature: {str(e)}"
        await ctx.error(errMsg)
        logger.error(errMsg, exc_info=True)
        resp_json["code"] = -1
        resp_json["errMsg"] = errMsg
        return resp_json

async def verify_signature(
        ctx: Context,
        message_string,
        signature_string
) -> Dict[str, Any]:
    
    resp_json = {}

    try:
        signature_bytes = base64.b64decode(signature_string)
    except Exception as e:
        error_msg = f"Failed verify signature, Base64 decoding of the signature failed: {e}"
        await ctx.error(error_msg)
        logger.error(error_msg, exc_info=True)
        resp_json["code"] = -1
        resp_json["errMsg"] = error_msg
        return resp_json
    public_key_path = get_global_public_key_path()
    if not public_key_path:
        error_msg = "Failed verify signature, public key file path not provided, ensure the 'BONUSPAY_PUBLIC_KEY_PATH' environment variable is set. "
        await ctx.error(error_msg)
        logger.error(error_msg, exc_info=True)
        resp_json["code"] = -1
        resp_json["errMsg"] = error_msg
        return resp_json
    public_key: Optional[RSAPrivateKey] = None
    try:
        public_key = load_public_key_from_path(public_key_path)
    except Exception as e:
        error_msg = f"Failed verify signature, Unable to load public key from path '{public_key_path}': {str(e)}"
        await ctx.error(error_msg)
        logger.error(error_msg, exc_info=True)
        resp_json["code"] = -1
        resp_json["errMsg"] = error_msg
        return resp_json

    if public_key is None:
        error_msg = "Failed signature, public key does not exist. "
        await ctx.error(error_msg)
        logger.error(error_msg, exc_info=True)
        resp_json["code"] = -1
        resp_json["errMsg"] = error_msg
        return resp_json


    try:
        encoded_message = message_string.encode('utf-8')
        public_key.verify(
            signature_bytes,
            encoded_message,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        resp_json["code"] = 0
        resp_json["errMsg"] = "success"
        return resp_json
    except Exception as e:
        error_msg = f"Failed verify signature, An error occurred while verification the signature: {str(e)}"
        await ctx.error(error_msg)
        logger.error(error_msg, exc_info=True)
        resp_json["code"] = -1
        resp_json["errMsg"] = error_msg
        return resp_json

async def _call_bonuspay_api(
    ctx: Context,
    api_path: str,
    biz_content: Dict[str, Any],
    request_time: int,
    language: str = "en"
) -> str:
    """
    A generic function for calling different endpoints of the BonusPay API.
    Handles request header and body construction, HTTP requests, logging, and generic response parsing.
    """
    api_base_url = get_api_base_url()
    api_full_url = f"{api_base_url}{api_path}"
    payload = {
        "requestTime": request_time,
        "bizContent": biz_content
    }
    partner_id = get_global_partner_id()
    resp_json = {}
    signature_resp = await generate_signature(ctx, payload)
    if signature_resp.get("code") != 0:
        resp_json["code"] = signature_resp.get("code", -1)
        resp_json["errMsg"] = signature_resp.get("errMsg", "Signature generation failed.")
        return json.dumps(resp_json, separators=(',', ':'), ensure_ascii=False)

    headers = {
        "Content-Language": language,
        "Content-Type": "application/json",
        "sign":  signature_resp.get("data"),
        "Partner-Id": partner_id
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(api_full_url, headers=headers, json=payload, timeout=30.0)
            response.raise_for_status()
            response_headers = response.headers 
            response_body = response.json()

            await ctx.debug(f"BonusPay API Request Header: {json.dumps(headers, indent=2, ensure_ascii=False)}")
            await ctx.debug(f"BonusPay API Request Body: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            await ctx.debug(f"BonusPay API Response Header: {json.dumps(dict(response_headers), indent=2, ensure_ascii=False)}")
            await ctx.debug(f"BonusPay API Response Body: {json.dumps(response_body, indent=2, ensure_ascii=False)}")

            logger.debug(f"BonusPay API Request Header:{json.dumps(headers)}")
            logger.debug(f"BonusPay API Request Body: {json.dumps(payload)}")
            logger.debug(f"BonusPay API Response Header: {json.dumps(dict(response_headers))}")
            logger.debug(f"BonusPay API Response Body: {json.dumps(response_body)}")

            body_head = response_body.get("head", {})
            if body_head.get("applyStatus") == "SUCCESS" and body_head.get("code") == "0":
                
                resp_sign = response_headers.get("sign")
                
                if resp_sign is None:
                    resp_json["code"] = -1
                    resp_json["errMsg"] = "API response missing signature header."
                    resp_json["data"] = {"status_code": response.status_code, "text_preview": response.text[:200]}
                    return json.dumps(resp_json, separators=(',', ':'), ensure_ascii=False)
                # verify response signature
                message_to_verify = json.dumps(response_body, separators=(',', ':'), ensure_ascii=False)
                verify_resp = await verify_signature(ctx, message_to_verify, resp_sign)
                if verify_resp.get("code") != 0: 
                    resp_json["code"] = verify_resp.get("code", -1) 
                    resp_json["errMsg"] = verify_resp.get("errMsg", "Response signature verification failed.")
                    return json.dumps(resp_json, separators=(',', ':'), ensure_ascii=False)
                resp_json["code"] = int(body_head.get("code"))
                resp_json["msg"] = body_head.get("msg")
                resp_json["data"] = response_body.get('body')
                return json.dumps(resp_json, separators=(',', ':'), ensure_ascii=False)
            else:
                error_msg = body_head.get("msg", "Unknown error")
                resp_json["code"] = int(body_head.get("code", -1))
                resp_json["errMsg"] = error_msg
                return json.dumps(resp_json, separators=(',', ':'), ensure_ascii=False)
        except httpx.HTTPStatusError as e:
            errMsg = f"Error: API returned status code: {e.response.status_code}, Response: {e.response.text}"
            await ctx.error(errMsg)
            logger.error(errMsg, exc_info=True)
            resp_json["code"] = e.response.status_code
            resp_json["errMsg"] = e.response.text
            return json.dumps(resp_json, separators=(',', ':'), ensure_ascii=False)
        except httpx.RequestError as e:
            errMsg = f"Error: A network error occurred while calling the API: {str(e)}"
            await ctx.error(errMsg)
            logger.error(errMsg, exc_info=True)
            resp_json["code"] = -1
            resp_json["errMsg"] = errMsg
            return json.dumps(resp_json, separators=(',', ':'), ensure_ascii=False)
        except Exception as e:
            errMsg = f"An unexpected error occurred: {str(e)}"
            await ctx.error(errMsg)
            logger.error(errMsg, exc_info=True)
            resp_json["code"] = -1
            resp_json["errMsg"] = errMsg
            return json.dumps(resp_json, separators=(',', ':'), ensure_ascii=False)

def bonuspay_server_overview() -> str:
    """
    Summary description of tools and use cases related to the BonusPay MCP Server.
    """
    return """
    The BonusPay MCP Server provides access to the BonusPay cryptocurrency payment platform API.
    You can leverage this server for the following main operations:
    - **Topup**: Manage customer cryptocurrency top-ups, e.g., get top-up addresses and query top-up orders.
    - **Payment**: Handle the creation, cancellation, acceptance, querying, and refund processes for payment orders.
    - **Withdraw/Transfer**: Manage merchant asset withdrawal and transfer operations, including creating withdrawal/transfer orders, querying orders, and supported networks.
    - **FX Rate**: Obtain real-time exchange rate information between cryptocurrencies and fiat currencies.
    - **Account Management**: View and manage the merchant's account asset list and balances.
    This server is designed to help you automate interactions with the BonusPay platform, simplifying cryptocurrency transaction and financial management processes.
    When a user's question involves any of the BonusPay platform operations mentioned above, please prioritize using the tools provided by this server.
    """
def add_overview_prompt(app_instance):
    app_instance.prompt()(bonuspay_server_overview)