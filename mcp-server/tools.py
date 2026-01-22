"""
Grist MCP Tools Module

Provides tool registry and execution for Grist data management tools.
Implements operations for listing tables and CRUD operations on records.
"""

from typing import Dict, Any, List, Optional
from grist_client import (
    make_grist_request,
    transform_table_response,
    transform_record_response,
    filter_record_fields
)


# Tool handler functions

async def grist_list_tables(arguments: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    List all tables in the Grist document.

    Args:
        arguments: Dict (no parameters required)

    Returns:
        List of table objects with id and name

    Example:
        tables = await grist_list_tables({})
        # Returns: [{"id": "Table1", "name": "Table1"}, {"id": "Customers", "name": "Customers"}]
    """
    # Make GET request to Grist API
    response = await make_grist_request("GET", "/tables")

    # Extract tables array from response
    grist_tables = response.get("tables", [])

    # Transform all tables to simplified format
    simplified_tables = [transform_table_response(table) for table in grist_tables]

    return simplified_tables


async def grist_list_records(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Retrieve records from a specific table.

    Args:
        arguments: Dict with required and optional parameters:
            - table_id (string, required): Table ID or name
            - limit (integer, optional): Number of records to retrieve (default: 100, max: 500)
            - filters (dict, optional): Filter conditions for records

    Returns:
        Dict with records array and metadata

    Raises:
        ValueError: If table_id is not provided or limit is out of range
    """
    # Get parameters
    table_id = arguments.get("table_id")
    limit = arguments.get("limit", 100)
    filters = arguments.get("filters")

    # Validate table_id is provided
    if not table_id:
        raise ValueError("table_id is required")

    # Validate limit is between 1 and 500
    if not isinstance(limit, int) or limit < 1 or limit > 500:
        raise ValueError("limit must be between 1 and 500")

    # Build query parameters
    params = {"limit": limit}
    if filters:
        # Grist API filter format - this can be expanded based on specific needs
        params["filter"] = filters

    # Make GET request to Grist API
    endpoint = f"/tables/{table_id}/records"
    response = await make_grist_request("GET", endpoint, params=params)

    # Transform records
    grist_records = response.get("records", [])
    simplified_records = [transform_record_response(record) for record in grist_records]

    return {
        "table_id": table_id,
        "records": simplified_records,
        "count": len(simplified_records)
    }


async def grist_create_records(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create new records in a table.

    Args:
        arguments: Dict with required parameters:
            - table_id (string, required): Table ID or name
            - records (array, required): Array of record objects with fields

    Returns:
        Dict with created records

    Raises:
        ValueError: If table_id or records are not provided, or records array is empty

    Example:
        result = await grist_create_records({
            "table_id": "Customers",
            "records": [
                {"Name": "John Doe", "Email": "john@example.com"},
                {"Name": "Jane Smith", "Email": "jane@example.com"}
            ]
        })
    """
    # Get parameters
    table_id = arguments.get("table_id")
    records = arguments.get("records")

    # Validate table_id is provided
    if not table_id:
        raise ValueError("table_id is required")

    # Validate records is provided and is a list
    if not records or not isinstance(records, list) or len(records) == 0:
        raise ValueError("records must be a non-empty array")

    # Transform records to Grist API format
    # Grist expects: {"records": [{"fields": {...}}, {"fields": {...}}]}
    grist_records = [{"fields": record} for record in records]

    # Make POST request to Grist API
    endpoint = f"/tables/{table_id}/records"
    data = {"records": grist_records}
    response = await make_grist_request("POST", endpoint, data=data)

    # Transform response records
    created_records = response.get("records", [])
    simplified_records = [transform_record_response(record) for record in created_records]

    return {
        "table_id": table_id,
        "created": simplified_records,
        "count": len(simplified_records)
    }


async def grist_update_records(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update existing records in a table.

    Args:
        arguments: Dict with required parameters:
            - table_id (string, required): Table ID or name
            - records (array, required): Array of records with id and fields to update

    Returns:
        Dict with success confirmation

    Raises:
        ValueError: If table_id or records are not provided, or records are invalid

    Example:
        result = await grist_update_records({
            "table_id": "Customers",
            "records": [
                {"id": 123, "fields": {"Email": "newemail@example.com"}},
                {"id": 456, "fields": {"Phone": "555-9999"}}
            ]
        })
    """
    # Get parameters
    table_id = arguments.get("table_id")
    records = arguments.get("records")

    # Validate table_id is provided
    if not table_id:
        raise ValueError("table_id is required")

    # Validate records is provided and is a list
    if not records or not isinstance(records, list) or len(records) == 0:
        raise ValueError("records must be a non-empty array")

    # Validate each record has id and fields
    for record in records:
        if "id" not in record:
            raise ValueError("Each record must have an 'id' field")
        if "fields" not in record:
            raise ValueError("Each record must have a 'fields' object")

    # Make PATCH request to Grist API
    endpoint = f"/tables/{table_id}/records"
    data = {"records": records}
    response = await make_grist_request("PATCH", endpoint, data=data)

    return {
        "table_id": table_id,
        "updated": len(records),
        "success": True
    }


async def grist_delete_records(arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Delete records from a table.

    Args:
        arguments: Dict with required parameters:
            - table_id (string, required): Table ID or name
            - record_ids (array, required): Array of record IDs to delete

    Returns:
        Dict with success confirmation

    Raises:
        ValueError: If table_id or record_ids are not provided, or array is empty

    Example:
        result = await grist_delete_records({
            "table_id": "Customers",
            "record_ids": [123, 456, 789]
        })
    """
    # Get parameters
    table_id = arguments.get("table_id")
    record_ids = arguments.get("record_ids")

    # Validate table_id is provided
    if not table_id:
        raise ValueError("table_id is required")

    # Validate record_ids is provided and is a list
    if not record_ids or not isinstance(record_ids, list) or len(record_ids) == 0:
        raise ValueError("record_ids must be a non-empty array")

    # Validate all IDs are integers
    for record_id in record_ids:
        if not isinstance(record_id, int):
            raise ValueError("All record_ids must be integers")

    # Make DELETE request to Grist API
    endpoint = f"/tables/{table_id}/records"
    data = {"records": record_ids}
    response = await make_grist_request("DELETE", endpoint, data=data)

    return {
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
    return {
        "grist_list_tables": {
            "description": "List all tables in the Grist document",
            "schema": {
                "type": "object",
                "properties": {},
                "required": []
            },
            "handler": grist_list_tables
        },
        "grist_list_records": {
            "description": "Retrieve records from a specific table with optional filters and limit",
            "schema": {
                "type": "object",
                "properties": {
                    "table_id": {
                        "type": "string",
                        "description": "Table ID or name"
                    },
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
                "required": ["table_id"]
            },
            "handler": grist_list_records
        },
        "grist_create_records": {
            "description": "Create new records in a table",
            "schema": {
                "type": "object",
                "properties": {
                    "table_id": {
                        "type": "string",
                        "description": "Table ID or name"
                    },
                    "records": {
                        "type": "array",
                        "description": "Array of record objects with field values",
                        "items": {
                            "type": "object"
                        }
                    }
                },
                "required": ["table_id", "records"]
            },
            "handler": grist_create_records
        },
        "grist_update_records": {
            "description": "Update existing records in a table by ID",
            "schema": {
                "type": "object",
                "properties": {
                    "table_id": {
                        "type": "string",
                        "description": "Table ID or name"
                    },
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
                "required": ["table_id", "records"]
            },
            "handler": grist_update_records
        },
        "grist_delete_records": {
            "description": "Delete records from a table by ID",
            "schema": {
                "type": "object",
                "properties": {
                    "table_id": {
                        "type": "string",
                        "description": "Table ID or name"
                    },
                    "record_ids": {
                        "type": "array",
                        "description": "Array of record IDs to delete",
                        "items": {
                            "type": "integer"
                        }
                    }
                },
                "required": ["table_id", "record_ids"]
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
    # Get tool registry
    registry = get_tool_registry()

    # Check if tool exists
    if tool_name not in registry:
        raise ValueError(f"Unknown tool: {tool_name}")

    # Get tool handler
    tool = registry[tool_name]
    handler = tool["handler"]

    # Execute tool
    result = await handler(arguments)

    return result
