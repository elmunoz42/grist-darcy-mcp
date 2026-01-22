# Grist MCP Server

Model Context Protocol (MCP) server that enables AI assistants like DarcyIQ to interact with Grist documents via the Grist REST API. Query tables, and create, read, update, and delete records through natural language conversation.

---

## Features

### Grist Data Management
- **List Tables** - Retrieve all tables in a Grist document
- **List Records** - Fetch records from a table with optional filters
- **Create Records** - Add new records to a table
- **Update Records** - Modify existing records by ID
- **Delete Records** - Remove records from a table

### MCP Protocol Features
- **JSON-RPC 2.0** - Standard protocol for AI tool integration
- **SSE Compatible** - Server-Sent Events support for DarcyIQ
- **Authentication** - API key-based security (MCP_AUTH_TOKEN + Grist API key)
- **Rate Limiting** - Built-in protection (30/min for list, 60/min for calls)
- **CORS Support** - Configurable cross-origin access
- **Health Monitoring** - Health check endpoint for uptime monitoring

### Security
- **Required Authentication** - MCP_AUTH_TOKEN required for all requests
- **Grist API Key** - Secure Grist API authentication
- **No Plugin Needed** - Works with standard Grist REST API
- **Environment-based Config** - Credentials stored in .env file

---

## Prerequisites

- **Python 3.9+**
- **Grist Instance** with:
  - Self-hosted or cloud-hosted Grist
  - API key from Profile Settings
  - Document ID for the Grist document to access
- **Server** (for deployment):
  - Ubuntu 20.04+ or similar Linux distribution
  - Public IP or domain name
  - Ports 22 (SSH) and 8000 (MCP) accessible

---

## Quick Start (Local Development)

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd grist-sqlite-ec2/mcp-server
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
nano .env  # Edit with your credentials
```

**Required environment variables:**
```bash
# Grist Configuration
GRIST_API_URL=https://docs.getgrist.com  # or your self-hosted URL
GRIST_API_KEY=your_grist_api_key_here
GRIST_DOC_ID=your_document_id_here

# MCP Server Configuration
MCP_SERVER_HOST=127.0.0.1  # localhost for dev
MCP_SERVER_PORT=8001       # or any available port

# Security (REQUIRED)
MCP_AUTH_TOKEN=your_generated_token_here
```

**Generate auth token:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 5. Get Grist API Key

1. Log into your Grist instance
2. Go to **Profile Settings** (top right menu)
3. Navigate to **API** section
4. Click **Create API Key**
5. Copy the generated key
6. Paste into `.env` as `GRIST_API_KEY`

### 6. Get Grist Document ID

Your document ID is in the URL when viewing a Grist document:
- URL format: `https://docs.getgrist.com/doc/DOCUMENT_ID`
- Example: `https://docs.getgrist.com/doc/abc123xyz456`
- Document ID: `abc123xyz456`

### 7. Test Grist Connection
```bash
cd utility-scripts
python test_grist_connection.py
```

Expected output:
```
✅ SUCCESS! Retrieved X tables
```

### 8. Run Tests
```bash
pytest -v
```

All tests should pass.

### 9. Start Server
```bash
python server.py
```

Server will start at `http://127.0.0.1:8001`

### 10. Test Endpoints
```bash
# Health check
curl http://localhost:8001/health

# Initialize MCP connection
curl -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -H "Authorization: api_key YOUR_AUTH_TOKEN" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}'

# List available tools
curl -X POST http://localhost:8001/ \
  -H "Content-Type: application/json" \
  -H "Authorization: api_key YOUR_AUTH_TOKEN" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
```

---

## Available Tools

### 1. grist_list_tables
List all tables in the Grist document.

**Parameters:** None

**Returns:** List of tables with id and name

**Example:**
```json
{
  "tool_name": "grist_list_tables",
  "arguments": {}
}
```

### 2. grist_list_records
Retrieve records from a specific table.

**Parameters:**
- `table_id` (string, required): Table ID or name
- `limit` (integer, optional): Number of records (default: 100, max: 500)
- `filters` (object, optional): Filter conditions

**Returns:** List of records with id and fields

**Example:**
```json
{
  "tool_name": "grist_list_records",
  "arguments": {
    "table_id": "Customers",
    "limit": 50
  }
}
```

### 3. grist_create_records
Add new records to a table.

**Parameters:**
- `table_id` (string, required): Table ID or name
- `records` (array, required): Array of record objects with field values

**Returns:** Created records with assigned IDs

**Example:**
```json
{
  "tool_name": "grist_create_records",
  "arguments": {
    "table_id": "Customers",
    "records": [
      {
        "Name": "John Doe",
        "Email": "john@example.com",
        "Phone": "555-1234"
      }
    ]
  }
}
```

### 4. grist_update_records
Update existing records in a table.

**Parameters:**
- `table_id` (string, required): Table ID or name
- `records` (array, required): Array of records with id and fields to update

**Returns:** Updated records

**Example:**
```json
{
  "tool_name": "grist_update_records",
  "arguments": {
    "table_id": "Customers",
    "records": [
      {
        "id": 123,
        "fields": {
          "Email": "newemail@example.com",
          "Phone": "555-9999"
        }
      }
    ]
  }
}
```

### 5. grist_delete_records
Delete records from a table.

**Parameters:**
- `table_id` (string, required): Table ID or name
- `record_ids` (array, required): Array of record IDs to delete

**Returns:** Success confirmation

**Example:**
```json
{
  "tool_name": "grist_delete_records",
  "arguments": {
    "table_id": "Customers",
    "record_ids": [123, 456]
  }
}
```

---

## DarcyIQ Integration

### Configure MCP Server in DarcyIQ

**Server Settings:**
```json
{
  "name": "Grist Data Manager",
  "url": "https://your-server-domain.com",
  "auth": {
    "type": "api_key",
    "token": "YOUR_MCP_AUTH_TOKEN"
  }
}
```

### Example Usage in DarcyIQ

> "List all tables in my Grist document"

> "Show me the first 10 records from the Customers table"

> "Add a new customer named Jane Smith with email jane@example.com"

> "Update customer ID 123 to change their phone number to 555-8888"

> "Delete customer records with IDs 456 and 789"

---

## Production Deployment

See **[EC2_DEPLOYMENT.md](EC2_DEPLOYMENT.md)** for deploying both Grist and the MCP server to AWS EC2.

Quick deployment overview:
1. Deploy Grist instance (Docker or self-hosted)
2. Deploy MCP server on same EC2 or separate instance
3. Configure `.env` with production values
4. Setup systemd service for auto-start
5. Configure Nginx reverse proxy + HTTPS
6. Integrate with DarcyIQ

---

## Architecture

```
┌─────────────┐
│   DarcyIQ   │
│  (AI Agent) │
└──────┬──────┘
       │ SSE/JSON-RPC 2.0
       │ (MCP Protocol)
       v
┌─────────────────────┐
│   MCP Server        │
│   (FastAPI/Python)  │
│   - Authentication  │
│   - Rate Limiting   │
│   - Tool Execution  │
└──────┬──────────────┘
       │ REST API
       │ (Grist API Key)
       v
┌─────────────────────┐
│   Grist Instance    │
│   - SQLite/Postgres │
│   - Documents       │
│   - Tables/Records  │
└─────────────────────┘
```

---

## Security

### Authentication Layers
1. **MCP Authentication**: MCP_AUTH_TOKEN required for all MCP requests
2. **Grist API Key**: Required for all Grist API requests
3. **HTTPS**: Encrypted transport in production

### Best Practices
- Never commit `.env` to version control
- Use strong random tokens for MCP_AUTH_TOKEN
- Restrict API key permissions in Grist
- Use CORS to limit allowed origins
- Enable rate limiting to prevent abuse
- Monitor logs for suspicious activity

---

## Testing

### Run All Tests
```bash
pytest -v
```

### Run Specific Test Suites
```bash
# Grist client tests
pytest test_grist_client.py -v

# Grist tools tests
pytest test_grist_tools.py -v

# Integration tests
pytest test_integration.py -v
```

---

## Troubleshooting

### Server Won't Start
```bash
# Check if MCP_AUTH_TOKEN is set
cat .env | grep MCP_AUTH_TOKEN

# Check logs
python server.py
```

### Grist Connection Fails
```bash
# Test connection
cd utility-scripts
python test_grist_connection.py

# Common issues:
# - Wrong GRIST_API_KEY
# - Invalid GRIST_DOC_ID
# - Grist instance not accessible
# - API key lacks permissions
```

### Authentication Errors
- Verify `MCP_AUTH_TOKEN` matches in both `.env` and DarcyIQ
- Check auth header format in requests
- Ensure Grist API key is valid and has proper permissions

---

## API Reference

### Grist REST API Endpoints Used

- `GET /api/docs/{docId}/tables` - List tables
- `GET /api/docs/{docId}/tables/{tableId}/records` - List records
- `POST /api/docs/{docId}/tables/{tableId}/records` - Create records
- `PATCH /api/docs/{docId}/tables/{tableId}/records` - Update records
- `DELETE /api/docs/{docId}/tables/{tableId}/records` - Delete records

**Authentication:** `Authorization: Bearer {GRIST_API_KEY}`

---

## Resources

- **Grist API Documentation**: https://support.getgrist.com/api/
- **Grist Help Center**: https://support.getgrist.com/
- **Model Context Protocol**: https://modelcontextprotocol.io/

---

**Sources:**
- [REST API reference - Grist Help Center](https://support.getgrist.com/api/)
- [Grist MCP Server by gwhthompson | Glama](https://glama.ai/mcp/servers/@gwhthompson/grist-mcp-server)
- [GitHub - gristlabs/grist-api: NodeJS client for interacting with Grist](https://github.com/gristlabs/grist-api)
- [GitHub - gristlabs/grist-core: Grist is the evolution of spreadsheets.](https://github.com/gristlabs/grist-core)

**Last Updated**: January 22, 2026
