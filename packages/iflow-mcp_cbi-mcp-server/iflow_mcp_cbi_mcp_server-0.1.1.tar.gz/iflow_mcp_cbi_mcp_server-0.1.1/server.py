#!/usr/bin/env python3
import os
import sys
import json
import asyncio
from typing import Optional
from dotenv import load_dotenv
import httpx

load_dotenv()

CLIENT_ID = os.getenv("CBI_CLIENT_ID")
CLIENT_SECRET = os.getenv("CBI_CLIENT_SECRET")
TIMEOUT = float(os.getenv("CBI_MCP_TIMEOUT", 120))
API_BASE = "https://api.cbinsights.com/v2"

# Validate required environment variables
if not CLIENT_ID or not CLIENT_SECRET:
    print(f"Warning: Missing required environment variables. CBI_CLIENT_ID={'set' if CLIENT_ID else 'not set'}, CBI_CLIENT_SECRET={'set' if CLIENT_SECRET else 'not set'}", file=sys.stderr)

def get_auth_token() -> str:
    if not CLIENT_ID or not CLIENT_SECRET:
        raise Exception("Missing required environment variables: CBI_CLIENT_ID and CBI_CLIENT_SECRET must be set")

    url = f"{API_BASE}/authorize"
    payload = {
        "clientId": CLIENT_ID,
        "clientSecret": CLIENT_SECRET
    }

    with httpx.Client() as client:
        try:
            response = client.post(url, json=payload, timeout=30.0)
            response.raise_for_status()
            return response.json()["token"]
        except Exception as e:
            raise Exception(f"Failed to authenticate: {str(e)}")

def chat_with_cbi(message: str, chat_id: Optional[str] = None) -> str:
    token = get_auth_token()
    url = f"{API_BASE}/chatcbi"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    payload = {"message": message}
    if chat_id:
        payload["chatID"] = chat_id

    with httpx.Client() as client:
        try:
            response = client.post(url, headers=headers, json=payload, timeout=TIMEOUT)
            response.raise_for_status()
            return response.text
        except Exception as e:
            raise Exception(str(e))

async def handle_request(request):
    """Handle MCP requests"""
    method = request.get("method")

    if method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "cbi-mcp-server",
                "version": "0.1.1"
            }
        }

    elif method == "tools/list":
        return {
            "tools": [
                {
                    "name": "ChatCBI",
                    "description": "Chat with CB Insights API for market intelligence and company research. Provide clear, specific queries for the best results. You can continue conversations by including the chat ID from previous interaction.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "The message to send to ChatCBI"
                            },
                            "chat_id": {
                                "type": "string",
                                "description": "Optional chat ID to continue a previous conversation"
                            }
                        },
                        "required": ["message"]
                    }
                }
            ]
        }

    elif method == "tools/call":
        params = request.get("params", {})
        name = params.get("name")
        arguments = params.get("arguments", {})

        if name == "ChatCBI":
            message = arguments.get("message", "")
            chat_id = arguments.get("chat_id")

            try:
                result = chat_with_cbi(message, chat_id)
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": result
                        }
                    ]
                }
            except Exception as e:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error: {str(e)}"
                        }
                    ]
                }
        else:
            raise ValueError(f"Unknown tool: {name}")

    else:
        raise ValueError(f"Unknown method: {method}")

async def main():
    """Main server loop"""
    while True:
        try:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            if not line:
                break

            request = json.loads(line.strip())
            request_id = request.get("id")

            try:
                result = await handle_request(request)
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
            except Exception as e:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32603,
                        "message": str(e)
                    }
                }

            print(json.dumps(response), flush=True)

        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Parse error: {str(e)}"
                }
            }
            print(json.dumps(error_response), flush=True)

if __name__ == "__main__":
    asyncio.run(main())