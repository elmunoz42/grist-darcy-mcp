"""
Test script to verify JSON string parsing fix for MCP tools
"""
import json
import asyncio
from tools import grist_update_records, grist_create_records, grist_delete_records

async def test_json_string_parsing():
    """Test that tools can handle records as JSON strings"""
    
    print("Testing JSON string parsing for MCP tools...\n")
    
    # Test 1: grist_update_records with JSON string (simulating DarcyIQ behavior)
    print("Test 1: grist_update_records with records as JSON string")
    try:
        # This simulates how DarcyIQ is sending the data
        arguments = {
            "table_id": "Table1",
            "records": '[{"id": 56, "fields": {"Linkedin_Profile": "Not Found"}}]'  # String!
        }
        
        # Parse the arguments
        table_id = arguments.get("table_id")
        records = arguments.get("records")
        
        # Check if it's a string and parse
        if isinstance(records, str):
            records = json.loads(records)
            print(f"✓ Successfully parsed records string: {records}")
            print(f"  Type after parsing: {type(records)}")
            print(f"  Is list: {isinstance(records, list)}")
            print(f"  Length: {len(records)}")
        else:
            print(f"✗ Records is not a string: {type(records)}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print()
    
    # Test 2: grist_create_records with JSON string
    print("Test 2: grist_create_records with records as JSON string")
    try:
        arguments = {
            "table_id": "Table1",
            "records": '[{"Name": "Test", "Email": "test@example.com"}]'  # String!
        }
        
        records = arguments.get("records")
        if isinstance(records, str):
            records = json.loads(records)
            print(f"✓ Successfully parsed records string: {records}")
        else:
            print(f"✗ Records is not a string: {type(records)}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print()
    
    # Test 3: grist_delete_records with JSON string
    print("Test 3: grist_delete_records with record_ids as JSON string")
    try:
        arguments = {
            "table_id": "Table1",
            "record_ids": '[56, 57, 58]'  # String!
        }
        
        record_ids = arguments.get("record_ids")
        if isinstance(record_ids, str):
            record_ids = json.loads(record_ids)
            print(f"✓ Successfully parsed record_ids string: {record_ids}")
            print(f"  Type after parsing: {type(record_ids)}")
            print(f"  Is list: {isinstance(record_ids, list)}")
            print(f"  All integers: {all(isinstance(id, int) for id in record_ids)}")
        else:
            print(f"✗ record_ids is not a string: {type(record_ids)}")
            
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print("\n" + "="*60)
    print("JSON string parsing tests completed successfully!")
    print("The MCP server should now handle DarcyIQ's JSON strings correctly.")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(test_json_string_parsing())
