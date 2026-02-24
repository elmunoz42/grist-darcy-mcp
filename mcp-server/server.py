"""
Grist MCP Server - FastAPI Server for DarcyIQ Integration

Model Context Protocol (MCP) server enabling AI agents to interact with
Grist documents via REST API for managing tables and records (CRUD operations).
"""

import os
import sys
import json
from typing import Dict, Any
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Validate required environment variables at startup
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN")
if not MCP_AUTH_TOKEN:
    print("ERROR: MCP_AUTH_TOKEN environment variable is required but not set")
    print("Please configure MCP_AUTH_TOKEN in your .env file")
    sys.exit(1)

GRIST_API_KEY = os.getenv("GRIST_API_KEY")
if not GRIST_API_KEY:
    print("ERROR: GRIST_API_KEY environment variable is required but not set")
    print("Please configure GRIST_API_KEY in your .env file")
    sys.exit(1)

GRIST_DOC_ID = os.getenv("GRIST_DOC_ID")
if not GRIST_DOC_ID:
    print("ERROR: GRIST_DOC_ID environment variable is required but not set")
    print("Please configure GRIST_DOC_ID in your .env file")
    sys.exit(1)

# Load Grist configuration
GRIST_API_URL = os.getenv("GRIST_API_URL", "https://docs.getgrist.com")

# Load server configuration with defaults
MCP_SERVER_HOST = os.getenv("MCP_SERVER_HOST", "0.0.0.0")
MCP_SERVER_PORT = int(os.getenv("MCP_SERVER_PORT", "8001"))

# Initialize FastAPI app
app = FastAPI(
    title="Grist MCP Server",
    description="Model Context Protocol server for Grist data management",
    version="1.0.0"
)

# Rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://darcyiq.com",
        "https://app.darcyiq.com",
        # Add your production domain here if deployed
        # "https://grist-mcp.yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)


@app.get("/")
async def root_get():
    """Root endpoint info - GET requests."""
    return {
        "service": "Grist MCP Server",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "mcp_protocol": "POST / with JSON-RPC 2.0",
            "description": "Model Context Protocol server for Grist table and record management"
        },
        "available_tools": [
            "grist_list_docs",
            "grist_set_context",
            "grist_get_context",
            "grist_list_tables",
            "grist_list_pages",
            "grist_list_records",
            "grist_create_records",
            "grist_update_records",
            "grist_delete_records"
        ],
        "grist_config": {
            "api_url": GRIST_API_URL,
            "doc_id": GRIST_DOC_ID,
            "api_key_configured": bool(GRIST_API_KEY)
        }
    }


@app.post("/")
@limiter.limit("60/minute")
async def mcp_protocol_handler(request: Request):
    """
    Handle MCP protocol requests via JSON-RPC 2.0.

    This is the primary endpoint for DarcyIQ integration.
    Supports initialize, notifications/initialized, tools/list, and tools/call methods.
    """
    # Verify API key - check both x-api-key and authorization headers
    x_api_key = request.headers.get("x-api-key")
    authorization = request.headers.get("authorization", "")

    # DarcyIQ sends: "api_key YOUR_TOKEN"
    # Also support Bearer format as fallback
    if authorization.startswith("api_key "):
        provided_key = authorization.replace("api_key ", "").strip()
    elif authorization.startswith("Bearer "):
        provided_key = authorization.replace("Bearer ", "").strip()
    elif x_api_key:
        provided_key = x_api_key
    else:
        provided_key = None

    # Verify authentication (MCP_AUTH_TOKEN is required at startup)
    if not provided_key or provided_key != MCP_AUTH_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Parse request body as JSON-RPC 2.0
    try:
        body_json = await request.json()
        # Log the request for debugging
        print(f"[MCP] Request: {json.dumps(body_json, indent=2)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail="Invalid JSON request body")

    method = body_json.get("method")
    params = body_json.get("params", {})
    request_id = body_json.get("id")  # JSON-RPC request ID (None for notifications)

    # Check if this is a notification (no id field) - these don't need a full response
    is_notification = request_id is None

    # Helper function to create JSON-RPC response
    def jsonrpc_response(result):
        if is_notification:
            return {"status": "acknowledged"}
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": result
        }

    # Helper function to create JSON-RPC error response
    def jsonrpc_error(code, message, data=None):
        if is_notification:
            return {"status": "error", "message": message}
        error = {"code": code, "message": message}
        if data:
            error["data"] = data
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": error
        }

    # Handle MCP methods
    if method == "initialize":
        return jsonrpc_response({
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "grist-mcp-server",
                "version": "1.0.0"
            }
        })

    elif method == "notifications/initialized":
        # This is a notification that initialization is complete
        return {"status": "acknowledged"}

    elif method == "tools/list":
        # Import tools module and get registry
        from tools import get_tool_registry

        # Get Grist tool registry
        grist_tools = get_tool_registry()

        # Transform registry to MCP tools list format
        tools_list = [
            {
                "name": name,
                "description": tool["description"],
                "inputSchema": tool["schema"]
            }
            for name, tool in grist_tools.items()
        ]

        return jsonrpc_response({"tools": tools_list})

    elif method == "tools/call":
        # Extract tool name and arguments from params
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        # Validate tool_name is provided
        if not tool_name:
            return jsonrpc_error(-32602, "Invalid params", "Missing tool name")

        # Execute the tool
        try:
            from tools import execute_tool
            result = await execute_tool(tool_name, arguments)

            # Wrap result in MCP format
            return jsonrpc_response({
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            })
        except ValueError as e:
            # Invalid parameters - return JSON-RPC error -32602
            return jsonrpc_error(-32602, "Invalid params", str(e))
        except Exception as e:
            # Internal/execution errors - return JSON-RPC error -32603
            return jsonrpc_error(-32603, "Internal error", str(e))

    # Handle other notification methods gracefully
    elif method and method.startswith("notifications/"):
        return {"status": "acknowledged"}

    else:
        return jsonrpc_error(-32601, "Method not found", f"Unknown method: {method}")


@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "grist_configured": bool(GRIST_API_KEY and GRIST_DOC_ID)
    }


if __name__ == "__main__":
    import uvicorn

    print(f"Starting Grist MCP Server on {MCP_SERVER_HOST}:{MCP_SERVER_PORT}")
    print(f"Health endpoint: http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}/health")
    print(f"MCP Protocol: POST http://{MCP_SERVER_HOST}:{MCP_SERVER_PORT}/ with JSON-RPC 2.0")
    print(f"Authentication: Required (MCP_AUTH_TOKEN configured: {'Yes' if MCP_AUTH_TOKEN else 'No'})")
    print(f"Grist Instance: {GRIST_API_URL}")
    print(f"Grist Document ID: {GRIST_DOC_ID}")

    uvicorn.run(app, host=MCP_SERVER_HOST, port=MCP_SERVER_PORT)
