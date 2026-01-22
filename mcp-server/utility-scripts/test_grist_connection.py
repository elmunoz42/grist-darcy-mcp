"""
Test Grist API Connection

Simple script to verify Grist API credentials and connectivity.
Run this before starting the MCP server to ensure configuration is correct.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path to import grist_client
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from grist_client import make_grist_request

# Load environment variables
load_dotenv()


async def test_connection():
    """Test Grist API connection by listing tables."""
    print("Testing Grist API connection...")
    print(f"API URL: {os.getenv('GRIST_API_URL', 'https://docs.getgrist.com')}")
    print(f"Document ID: {os.getenv('GRIST_DOC_ID', 'Not set')}")
    print(f"API Key configured: {'Yes' if os.getenv('GRIST_API_KEY') else 'No'}")
    print()

    try:
        # Try to list tables in the document
        response = await make_grist_request("GET", "/tables")
        tables = response.get("tables", [])

        print(f"✅ SUCCESS! Retrieved {len(tables)} table(s)")
        print()
        if tables:
            print("Tables found:")
            for table in tables:
                table_id = table.get("id", "Unknown")
                print(f"  - {table_id}")
        else:
            print("No tables found in document (this is okay for empty documents)")

        print()
        print("Your Grist API connection is working correctly!")
        return True

    except ValueError as e:
        print(f"❌ ERROR: {str(e)}")
        print()
        print("Common issues:")
        print("  - Check GRIST_API_KEY is valid (from Profile Settings -> API)")
        print("  - Check GRIST_DOC_ID matches your document URL")
        print("  - Check GRIST_API_URL is correct")
        print("  - Ensure API key has access to the document")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    # Run the test
    success = asyncio.run(test_connection())
    sys.exit(0 if success else 1)
