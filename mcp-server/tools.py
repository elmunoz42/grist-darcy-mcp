"""
Grist MCP Tools Module

Provides tool registry and execution for Grist data management tools.
Implements operations for listing tables and CRUD operations on records.
"""

import json
from typing import Dict, Any, List
from grist_client import (
    make_grist_request,
    transform_table_response,
    transform_record_response,
    resolve_doc_id,
    set_active_context_doc_id,
    get_active_context_doc_id,
    get_allowed_docs,
    get_default_doc_id,
)


def _get_doc_id(arguments: Dict[str, Any]) -> str:
    """Resolve doc_id from arguments/context/default with validation."""
    return resolve_doc_id(arguments.get("doc_id"))


def _get_table_id(arguments: Dict[str, Any]) -> str:
    """Resolve table/page identifier from tool arguments."""
    table_id = arguments.get("table_id")
    page_id = arguments.get("page_id")
    resolved = table_id or page_id
    if not resolved:
        raise ValueError("table_id or page_id is required")
    if not isinstance(resolved, str):
        raise ValueError("table_id or page_id must be a string")
    return resolved


# Tool handler functions

async def grist_list_docs(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """List documents this MCP instance may access."""
    docs = get_allowed_docs()
    if not docs:
        default_doc = get_default_doc_id()
        if not default_doc:
            raise ValueError("GRIST_DOC_ID environment variable is not set")
        docs = [{"id": default_doc, "name": default_doc}]

    active_doc = get_active_context_doc_id()
    return [
        {
            "id": doc["id"],
            "name": doc.get("name", doc["id"]),
            "active": bool(active_doc and active_doc == doc["id"])
        }
        for doc in docs
    ]


async def grist_set_context(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Set active document context for subsequent tool calls."""
    doc_id = arguments.get("doc_id")
    if not doc_id:
        raise ValueError("doc_id is required")

    active_doc = set_active_context_doc_id(doc_id)
    return {
        "active_doc_id": active_doc,
        "default_doc_id": get_default_doc_id()
    }


async def grist_get_context(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Return active and default document context."""
    active_doc = get_active_context_doc_id()
    default_doc = get_default_doc_id()

    return {
        "active_doc_id": active_doc,
        "default_doc_id": default_doc,
        "effective_doc_id": active_doc or default_doc
    }


async def grist_list_tables(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    List all tables in the Grist document.

    Args:
        arguments: Dict (optional: doc_id)

    Returns:
        List of table objects with id and name
    """
    doc_id = _get_doc_id(arguments)

    response = await make_grist_request("GET", "/tables", doc_id=doc_id)
    grist_tables = response.get("tables", [])
    simplified_tables = [transform_table_response(table) for table in grist_tables]

    return simplified_tables


async def grist_list_pages(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """List page-like table entries for a document."""
    doc_id = _get_doc_id(arguments)
    tables = await grist_list_tables({"doc_id": doc_id})

    return {
        "doc_id": doc_id,
        "pages": [
            {
                "page_id": table["id"],
                "name": table["name"]
            }
            for table in tables
        ],
        "count": len(tables)
    }


async def grist_list_records(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve records from a specific table.

    Args:
        arguments: Dict with required and optional parameters:
            - table_id or page_id (string, required): Table ID/name or page alias
            - doc_id (string, optional): Target Grist document
            - limit (integer, optional): Number of records to retrieve (default: 100, max: 500)
            - filters (dict, optional): Filter conditions for records

    Returns:
        Dict with records array and metadata
    """
    doc_id = _get_doc_id(arguments)
    table_id = _get_table_id(arguments)
    limit = arguments.get("limit", 100)
    filters = arguments.get("filters")

    if not isinstance(limit, int) or limit < 1 or limit > 500:
        raise ValueError("limit must be between 1 and 500")

    params = {"limit": limit}
    if filters:
        params["filter"] = filters

    endpoint = f"/tables/{table_id}/records"
    response = await make_grist_request("GET", endpoint, params=params, doc_id=doc_id)

    grist_records = response.get("records", [])
    simplified_records = [transform_record_response(record) for record in grist_records]

    return {
        "doc_id": doc_id,
        "table_id": table_id,
        "records": simplified_records,
        "count": len(simplified_records)
    }


async def grist_create_records(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create new records in a table.

    Args:
        arguments: Dict with required parameters:
            - table_id or page_id (string, required)
            - doc_id (string, optional)
            - records (array, required)

    Returns:
        Dict with created records
    """
    doc_id = _get_doc_id(arguments)
    table_id = _get_table_id(arguments)
    records = arguments.get("records")

    if isinstance(records, str):
        try:
            records = json.loads(records)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"records parameter is a string but not valid JSON: {e}")

    if not records or not isinstance(records, list):
        raise ValueError("records must be a non-empty array")

    grist_records = [{"fields": record} for record in records]
    endpoint = f"/tables/{table_id}/records"
    data = {"records": grist_records}
    response = await make_grist_request("POST", endpoint, data=data, doc_id=doc_id)

    created_records = response.get("records", [])
    simplified_records = [transform_record_response(record) for record in created_records]

    return {
        "doc_id": doc_id,
        "table_id": table_id,
        "created": simplified_records,
        "count": len(simplified_records)
    }


async def grist_update_records(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update existing records in a table.

    Args:
        arguments: Dict with required parameters:
            - table_id or page_id (string, required)
            - doc_id (string, optional)
            - records (array, required): Array of records with id and fields

    Returns:
        Dict with success confirmation
    """
    doc_id = _get_doc_id(arguments)
    table_id = _get_table_id(arguments)
    records = arguments.get("records")

    if isinstance(records, str):
        try:
            records = json.loads(records)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"records parameter is a string but not valid JSON: {e}")

    if not records or not isinstance(records, list):
        raise ValueError("records must be a non-empty array")

    for record in records:
        if "id" not in record:
            raise ValueError("Each record must have an 'id' field")
        if "fields" not in record:
            raise ValueError("Each record must have a 'fields' object")

    endpoint = f"/tables/{table_id}/records"
    data = {"records": records}
    await make_grist_request("PATCH", endpoint, data=data, doc_id=doc_id)

    return {
        "doc_id": doc_id,
        "table_id": table_id,
        "updated": len(records),
        "success": True
    }


async def grist_delete_records(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Delete records from a table.

    Args:
        arguments: Dict with required parameters:
            - table_id or page_id (string, required)
            - doc_id (string, optional)
            - record_ids (array, required)

    Returns:
        Dict with success confirmation
    """
    doc_id = _get_doc_id(arguments)
    table_id = _get_table_id(arguments)
    record_ids = arguments.get("record_ids")

    if isinstance(record_ids, str):
        try:
            record_ids = json.loads(record_ids)
        except (json.JSONDecodeError, TypeError) as e:
            raise ValueError(f"record_ids parameter is a string but not valid JSON: {e}")

    if not record_ids or not isinstance(record_ids, list):
        raise ValueError("record_ids must be a non-empty array")

    for record_id in record_ids:
        if not isinstance(record_id, int):
            raise ValueError("All record_ids must be integers")

    endpoint = f"/tables/{table_id}/records"
    data = {"records": record_ids}
    await make_grist_request("DELETE", endpoint, data=data, doc_id=doc_id)

    return {
        "doc_id": doc_id,
        "table_id": table_id,
        "deleted": len(record_ids),
        "success": True
    }


# Tool Registry

def get_tool_registry() -> Dict[str, Dict[str, Any]]:
    """
    Get the registry of all available Grist MCP tools.

    Returns:
        Dict mapping tool names to their definitions (description, schema, handler)
    """
    doc_id_schema = {
        "type": "string",
        "description": "Optional Grist document ID. If omitted, uses active context or GRIST_DOC_ID."
    }

    table_or_page_props = {
        "table_id": {
            "type": "string",
            "description": "Table ID or name"
        },
        "page_id": {
            "type": "string",
            "description": "Page alias (treated as table_id)"
        },
        "doc_id": doc_id_schema
    }

    return {
        "grist_list_docs": {
            "description": "List documents available to this MCP instance",
            "schema": {
                "type": "object",
                "properties": {},
                "required": []
            },
            "handler": grist_list_docs
        },
        "grist_set_context": {
            "description": "Set the active Grist document context",
            "schema": {
                "type": "object",
                "properties": {
                    "doc_id": {
                        "type": "string",
                        "description": "Document ID to set as active context"
                    }
                },
                "required": ["doc_id"]
            },
            "handler": grist_set_context
        },
        "grist_get_context": {
            "description": "Get current document context",
            "schema": {
                "type": "object",
                "properties": {},
                "required": []
            },
            "handler": grist_get_context
        },
        "grist_list_tables": {
            "description": "List all tables in a Grist document",
            "schema": {
                "type": "object",
                "properties": {
                    "doc_id": doc_id_schema
                },
                "required": []
            },
            "handler": grist_list_tables
        },
        "grist_list_pages": {
            "description": "List page-like table entries in a Grist document",
            "schema": {
                "type": "object",
                "properties": {
                    "doc_id": doc_id_schema
                },
                "required": []
            },
            "handler": grist_list_pages
        },
        "grist_list_records": {
            "description": "Retrieve records from a specific table/page with optional filters and limit",
            "schema": {
                "type": "object",
                "properties": {
                    **table_or_page_props,
                    "limit": {
                        "type": "integer",
                        "description": "Number of records to retrieve (default: 100, max: 500)",
                        "minimum": 1,
                        "maximum": 500
                    },
                    "filters": {
                        "type": "object",
                        "description": "Optional filter conditions for records"
                    }
                },
                "required": []
            },
            "handler": grist_list_records
        },
        "grist_create_records": {
            "description": "Create new records in a table/page",
            "schema": {
                "type": "object",
                "properties": {
                    **table_or_page_props,
                    "records": {
                        "type": "array",
                        "description": "Array of record objects with field values",
                        "items": {
                            "type": "object"
                        }
                    }
                },
                "required": ["records"]
            },
            "handler": grist_create_records
        },
        "grist_update_records": {
            "description": "Update existing records in a table/page by ID",
            "schema": {
                "type": "object",
                "properties": {
                    **table_or_page_props,
                    "records": {
                        "type": "array",
                        "description": "Array of records with id and fields to update",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {
                                    "type": "integer",
                                    "description": "Record ID"
                                },
                                "fields": {
                                    "type": "object",
                                    "description": "Fields to update"
                                }
                            },
                            "required": ["id", "fields"]
                        }
                    }
                },
                "required": ["records"]
            },
            "handler": grist_update_records
        },
        "grist_delete_records": {
            "description": "Delete records from a table/page by ID",
            "schema": {
                "type": "object",
                "properties": {
                    **table_or_page_props,
                    "record_ids": {
                        "type": "array",
                        "description": "Array of record IDs to delete",
                        "items": {
                            "type": "integer"
                        }
                    }
                },
                "required": ["record_ids"]
            },
            "handler": grist_delete_records
        }
    }


async def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Any:
    """
    Execute a Grist tool by name with given arguments.

    Args:
        tool_name: Name of the tool to execute
        arguments: Arguments to pass to the tool

    Returns:
        Result from tool execution

    Raises:
        ValueError: If tool name is unknown or execution fails
    """
    registry = get_tool_registry()

    # Some MCP clients send null for tools with no args; normalize to empty object.
    if arguments is None:
        arguments = {}
    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be an object")

    if tool_name not in registry:
        raise ValueError(f"Unknown tool: {tool_name}")

    tool = registry[tool_name]
    handler = tool["handler"]

    return await handler(arguments)
