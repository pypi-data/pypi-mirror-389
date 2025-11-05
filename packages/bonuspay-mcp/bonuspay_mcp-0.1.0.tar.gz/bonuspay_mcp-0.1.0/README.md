# BonusPay MCP Installation and Usage Guide

## Requirements
- Python 3.8+
- MCP SDK 0.1.0+

## Download
```sh
# Download
git clone https://gitlab.platon.network/topos/bonuspay-mcp-server.git
# Enter project root directory
cd bonuspay-mcp-server
```

## Set up Environment

```sh
# Create virtual environment .venv
uv venv
# Activate environment
source .venv/bin/activate
```

## Install Dependencies

```sh
uv sync
```

## Supplemental (Install uv on Ubuntu)

```sh
# Download and install uv
curl -LsSf https://astral.sh/uv/install.sh | sh
# Make uv command effective
source $HOME/.local/bin/env
# Check version
uv --version
```

## Environment Variable Settings

```sh
export BONUSPAY_PRIVATE_KEY_PATH="your merchant private key file path"
export BONUSPAY_PUBLIC_KEY_PATH="your bonuspay public key file path"
export BONUSPAY_PARTNER_ID="your bonuspay partner id (merchant id)"
```

## Launch mcp server using uv

```sh
# (Execute in project root directory)
# ${mode}:             MCP Server Protocol: stdio, sse, streamable-http
# ${network}:          Network environment identifier, test for testnet; main for mainnet (if --network parameter is not provided, defaults to testnet)
# ${host}:             Service IP (if --host is not provided, defaults to 0.0.0.0)
# ${port}:             Service port (if --port is not provided, defaults to 9998)
# ${private-key-path}: Path to BonusPay merchant's RSA private key file (xx.pem) (defaults to value of environment variable BONUSPAY_PRIVATE_KEY_PATH)
# ${public-key-path}:  Path to BonusPay platform's RSA public key file (xx.pem) (defaults to value of environment variable BONUSPAY_PUBLIC_KEY_PATH)
# ${partner-id}:       BonusPay merchant's Partner ID (defaults to value of environment variable BONUSPAY_PARTNER_ID)
uv run -m bonuspay ${mode} --network ${network} --host ${host} --port ${port} --private-key-path ${private-key-path} --public-key-path ${public-key-path} --partner-id ${partner-id}
```

## Package and launch mcp server using uvx

```sh
# Clear local cache
rm -rf dist/
uv cache clean
# Package
uvx hatch build
# View package info (optional)
unzip -l dist/bonuspay-mcp-${version}-py3-none-any.whl
# Upload to PyPi
# ${PyPi-url}:  PyPi link, Testnet: https://test.pypi.org/legacy/; Mainnet:   https://pypi.org/legacy/
# ${token}:     PyPi API token
uv publish --publish-url ${PyPi-url} --token ${token}
# Launch Testnet (e.g., testnet package using mainnet dependencies)
uvx --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ bonuspay-mcp sse
# Launch Mainnet
uvx bonuspay-mcp sse
```

## Debug remote mcp server (sse) using MCP Inspector on PC

```sh
# Server-side
#
# 1. Activate virtual environment
uv venv
source .venv/bin/activate
# 2. Set PYTHONPATH environment variable
export PYTHONPATH=$PWD
# 3. Set ALLOWED_ORIGINS environment variable
export ALLOWED_ORIGINS="http://localhost:8082,http://127.0.0.1:8082,http://localhost:6274,http://127.0.0.1:6274,http://localhost:8083,http://127.0.0.1:8083"
# 4. Set server's proxy whitelist
export no_proxy="localhost,127.0.0.1,${ServerIp},api.testbonuspay.network"
echo $HTTP_PROXY
echo $no_proxy
# 5. Run mcp inspector for debugging (execute in project root directory)
mcp dev run_server_for_mcp_dev.py --with-editable .     # shell 1
npx @modelcontextprotocol/inspector                     # shell 2

# PC-side
#
# 1. Execute in local PC's bash (Open SSH tunnel, e.g., local 8082 binds server 6274, local 8083 binds server 6277, keep this bash open)
ssh -L 8082:127.0.0.1:6274 -L 8083:127.0.0.1:6277 your_username@your_ip
# 2. Open in local PC's browser
# ${token}: Token from the npx @modelcontextprotocol/inspector console in shell 2
http://localhost:8082/?MCP_PROXY_AUTH_TOKEN=${token}#tools
# 3. In Transport Type, enter sse; In URL, enter something like: http://${ServerIp}:${mcp server port}/sse; Click "Connect"
#
# 4. Start debugging
```

## Integrate with Cursor using source code (stdio mode)

```sh
# Download code locally
git clone https://gitlab.platon.network/topos/bonuspay-mcp-server.git
# Enter project root directory
cd bonuspay-mcp-server
# Create virtual environment .venv
uv venv
# Activate environment
source .venv/bin/activate
# Install project
uv pip install -e .
```

```json
// Configure Cursor Settings
{
  "mcpServers": {
    "bonuspay": {
      "name":"BonusPay API MCP Service",
      "type": "stdio",
      "isActive": true,
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "D:\\py-workspace\\bonuspay-mcp-server",
        "-m",
        "bonuspay"
      ],
      "env": {
        "BONUSPAY_PRIVATE_KEY_PATH": "Fill in your merchant private key file path",
        "BONUSPAY_PUBLIC_KEY_PATH":"Fill in your bonuspay public key file path",
        "BONUSPAY_PARTNER_ID":"Fill in your partner id (merchant id)"
      }
    }
  }
}
```

## Integrate with Cursor using package (stdio mode)

```json
// Testnet
{
  "mcpServers": {
    "bonuspay": {
      "name":"BonusPay MCP Service",
      "type": "stdio",
      "isActive": true,
      "command": "uvx",
      "args": [
        "--index-url",
        "https://test.pypi.org/simple/",
        "--extra-index-url",
        "https://pypi.org/simple/",
        "bonuspay-mcp",
        "stdio",
        "--network",
        "test"
      ],
      "env": {
        "BONUSPAY_PRIVATE_KEY_PATH": "Fill in your merchant private key file path",
        "BONUSPAY_PUBLIC_KEY_PATH":"Fill in your bonuspay public key file path",
        "BONUSPAY_PARTNER_ID":"Fill in your partner id (merchant id)"
      }
    }
  }
}
// Mainnet
{
  "mcpServers": {
    "bonuspay": {
      "name":"BonusPay MCP Service",
      "type": "stdio",
      "isActive": true,
      "command": "uvx",
      "args": [
        "bonuspay-mcp",
        "stdio",
        "--network",
        "main"
      ],
      "env": {
        "BONUSPAY_PRIVATE_KEY_PATH": "Fill in your merchant private key file path",
        "BONUSPAY_PUBLIC_KEY_PATH":"Fill in your bonuspay public key file path",
        "BONUSPAY_PARTNER_ID":"Fill in your partner id (merchant id)"
      }
    }
  }
}
```

## Integrate remote service with Cursor (sse mode)

```json
{
  "mcpServers": {
    "bonuspay": {
      "name":"BonusPay API MCP Service",
      "type": "sse",
      "isActive": true,
      "url":"http://${ServiceIp}:${ServicePort}/sse"
    }
  }
}
```

## Integrate remote service with Cursor (streamable-http mode)

```json
{
  "mcpServers": {
    "bonuspay": {
      "name":"BonusPay API MCP Service",
      "type": "streamable-http",
      "isActive": true,
      "url":"http://${ServiceIp}:${ServicePort}/mcp"
    }
  }
}
```