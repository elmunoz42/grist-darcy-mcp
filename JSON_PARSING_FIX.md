# JSON String Parsing Fix for DarcyIQ Integration

## Problem

DarcyIQ AI agent was encountering errors when trying to update Grist records via the MCP server:

```
Error calling MCP tool grist_update_records: unhandled errors in a TaskGroup (1 sub-exception)
First sub-exception: unhandled errors in a TaskGroup (1 sub-exception)
Caused by: None
```

### Root Cause

The agent was passing the `records` parameter as a **JSON string** instead of an actual JSON array:

**Incorrect (what DarcyIQ was sending):**
```json
{
  "table_id": "Table1",
  "records": "[{\"id\": 56, \"fields\": {\"Linkedin_Profile\": \"Not Found\"}}]"
}
```

**Correct (what the server expected):**
```json
{
  "table_id": "Table1",
  "records": [{"id": 56, "fields": {"Linkedin_Profile": "Not Found"}}]
}
```

Notice the difference: `"[{...}]"` (string) vs `[{...}]` (actual array).

## Solution

Updated the MCP tools to automatically detect and parse JSON strings:

### Changes Made

1. **Added JSON import** to [tools.py](mcp-server/tools.py#L8)

2. **Updated `grist_create_records`** to parse JSON strings:
   ```python
   # Parse records if it's a JSON string (common issue with some MCP clients)
   if isinstance(records, str):
       try:
           records = json.loads(records)
       except (json.JSONDecodeError, TypeError) as e:
           raise ValueError(f"records parameter is a string but not valid JSON: {e}")
   ```

3. **Updated `grist_update_records`** with the same parsing logic

4. **Updated `grist_delete_records`** to parse `record_ids` if it's a JSON string

## Files Modified

- [mcp-server/tools.py](mcp-server/tools.py) - Added JSON string parsing to all record functions

## Testing

Run the included test script to verify the fix:

```bash
cd mcp-server
python3 test_json_parsing.py
```

Expected output:
```
✓ Successfully parsed records string
✓ Successfully parsed records string  
✓ Successfully parsed record_ids string
JSON string parsing tests completed successfully!
```

## Next Steps

1. **Restart the MCP server** to apply the changes:
   ```bash
   # If running as systemd service
   sudo systemctl restart grist-mcp-server
   
   # Or if running manually
   cd mcp-server
   python3 server.py
   ```

2. **Test with DarcyIQ** - The agent should now successfully update records without errors

3. **Monitor logs** for any other issues

## Additional Notes

This fix is **backward compatible** - it still accepts properly formatted JSON arrays while also handling JSON strings. The server will work correctly with both formats.

### Why This Happens

Some MCP clients (like DarcyIQ) may serialize complex parameters as JSON strings when making HTTP requests. This is a common issue in API integrations where nested JSON objects need special handling.

### Error Prevention

The fix includes helpful error messages if the JSON string is malformed:
```
ValueError: records parameter is a string but not valid JSON: Expecting value: line 1 column 1 (char 0)
```

This makes debugging easier if there are any JSON formatting issues.
