"""
Grist REST API Client

Provides functions for authenticating with Grist and making API requests.
Handles Grist API key authentication, error handling, and response transformation.
"""

import os
import requests
from typing import Dict, Any, Optional, List


def get_grist_auth_header() -> Dict[str, str]:
    """
    Create Grist API authentication header.

    Uses GRIST_API_KEY from environment variables to create Bearer token header.

    Returns:
        Dict with Authorization header for Grist REST API

    Example:
        {"Authorization": "Bearer your_api_key_here"}
    """
    api_key = os.getenv("GRIST_API_KEY", "")

    if not api_key:
        raise ValueError("GRIST_API_KEY environment variable is not set")

    return {"Authorization": f"Bearer {api_key}"}


async def make_grist_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Make authenticated request to Grist REST API.

    Args:
        method: HTTP method (GET, POST, PATCH, DELETE)
        endpoint: API endpoint path (e.g., '/tables', '/tables/TableName/records')
        data: Optional request body data for POST/PATCH requests
        params: Optional query parameters for GET requests

    Returns:
        JSON response from Grist API

    Raises:
        ValueError: For authentication failures, permission errors, not found errors, or connection issues

    Example:
        result = await make_grist_request('GET', '/tables')
        result = await make_grist_request('POST', '/tables/Customers/records',
                                          data={'records': [{'fields': {...}}]})
    """
    grist_api_url = os.getenv("GRIST_API_URL", "https://docs.getgrist.com")
    grist_doc_id = os.getenv("GRIST_DOC_ID", "")

    if not grist_doc_id:
        raise ValueError("GRIST_DOC_ID environment variable is not set")

    # Build full URL
    base_url = grist_api_url.rstrip('/')
    full_url = f"{base_url}/api/docs/{grist_doc_id}{endpoint}"

    # Get Grist auth headers
    headers = get_grist_auth_header()
    headers["Content-Type"] = "application/json"

    # Set timeout for all requests
    timeout = 30

    try:
        # Make request based on method
        if method.upper() == "GET":
            response = requests.get(full_url, headers=headers, params=params, timeout=timeout)
        elif method.upper() == "POST":
            response = requests.post(full_url, headers=headers, json=data, timeout=timeout)
        elif method.upper() == "PATCH":
            response = requests.patch(full_url, headers=headers, json=data, timeout=timeout)
        elif method.upper() == "DELETE":
            response = requests.delete(full_url, headers=headers, json=data, timeout=timeout)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        # Handle HTTP errors with specific messages
        if response.status_code == 401:
            raise ValueError("Invalid Grist API key - check GRIST_API_KEY in .env")
        elif response.status_code == 403:
            raise ValueError("Insufficient permissions to perform this action on Grist document")
        elif response.status_code == 404:
            # Extract resource info from endpoint
            resource = endpoint.strip('/').split('/')[-1] if endpoint else "unknown"
            raise ValueError(f"Resource '{resource}' not found in Grist document")
        elif response.status_code >= 400:
            # Other HTTP errors
            error_msg = f"Grist API error: {response.status_code}"
            try:
                error_data = response.json()
                if "error" in error_data:
                    error_msg = f"{error_msg} - {error_data['error']}"
                elif "message" in error_data:
                    error_msg = f"{error_msg} - {error_data['message']}"
            except:
                pass
            raise ValueError(error_msg)

        # Return JSON response
        return response.json()

    except requests.exceptions.ConnectionError as e:
        raise ValueError(f"Unable to connect to Grist instance at {grist_api_url}")
    except requests.exceptions.Timeout as e:
        raise ValueError(f"Grist API request timed out after {timeout} seconds")
    except ValueError:
        # Re-raise ValueError exceptions (our custom error messages)
        raise
    except Exception as e:
        # Catch any other unexpected errors
        raise ValueError(f"Grist API request failed: {str(e)}")


def transform_table_response(grist_table: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform Grist API table response to simplified format.

    Args:
        grist_table: Raw Grist API table response

    Returns:
        Simplified table dict with id and name

    Example:
        grist_table = {"id": "Table1", ...}
        simplified = transform_table_response(grist_table)
        # Returns: {"id": "Table1", "name": "Table1"}
    """
    return {
        "id": grist_table.get("id", ""),
        "name": grist_table.get("id", "")  # Grist uses id as table name
    }


def transform_record_response(grist_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform Grist API record response to simplified format.

    Args:
        grist_record: Raw Grist API record response

    Returns:
        Record dict with id and fields

    Example:
        grist_record = {"id": 123, "fields": {"Name": "John", "Email": "john@example.com"}}
        simplified = transform_record_response(grist_record)
        # Returns: {"id": 123, "fields": {...}}
    """
    return {
        "id": grist_record.get("id", 0),
        "fields": grist_record.get("fields", {})
    }


def filter_record_fields(record: Dict[str, Any], fields: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Filter record object to include only specified fields.

    Args:
        record: Transformed record dict with id and fields
        fields: List of field names to include. If None, returns all fields.

    Returns:
        Record dict with only requested fields

    Example:
        record = {"id": 1, "fields": {"Name": "John", "Email": "john@example.com", "Phone": "555-1234"}}
        filter_record_fields(record, ["Name", "Email"])
        # Returns: {"id": 1, "fields": {"Name": "John", "Email": "john@example.com"}}
    """
    if fields is None:
        return record

    # Filter fields to only include requested ones
    filtered_fields = {key: record["fields"][key] for key in fields if key in record["fields"]}

    return {
        "id": record["id"],
        "fields": filtered_fields
    }
