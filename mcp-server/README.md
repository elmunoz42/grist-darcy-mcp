# Grist MCP Server

Model Context Protocol server for AI assistant integration with Grist documents.

---

## Quick Start

### 1. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
```bash
cp .env.example .env
nano .env
```

Set required variables:
- `MCP_AUTH_TOKEN` - Generate with `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
- `GRIST_API_URL` - Your Grist instance URL (default: https://docs.getgrist.com)
- `GRIST_API_KEY` - From Grist Profile Settings → API
- `GRIST_DOC_ID` - Default document ID from document URL

Optional for multi-document mode:
- `GRIST_ALLOWED_DOCS_JSON` - JSON array allowlist of docs, e.g.
  - `[{"id":"docA123","name":"Demo Sales"},{"id":"docB456","name":"Demo Ops"}]`

### 4. Test Connection
```bash
cd utility-scripts
python test_grist_connection.py
```

### 5. Start Server
```bash
python server.py
```

Server runs at `http://localhost:8001`

---

## Available Tools

- `grist_list_docs` - List documents available to the MCP instance
- `grist_set_context` - Set active document context
- `grist_get_context` - Get active/default document context
- `grist_list_tables` - List all tables
- `grist_list_pages` - List page-like table entries
- `grist_list_records` - Get records from a table
- `grist_create_records` - Add new records
- `grist_update_records` - Update existing records
- `grist_delete_records` - Delete records

---

## Documentation

See **[../MCP_SERVER.md](../MCP_SERVER.md)** for complete documentation.

---

## Project Structure

```
mcp-server/
├── server.py                          # FastAPI MCP server
├── grist_client.py                    # Grist REST API client
├── tools.py                           # MCP tools for Grist operations
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment template
├── README.md                          # This file
├── utility-scripts/
│   └── test_grist_connection.py       # Connection test script
└── tests/
    ├── test_grist_client.py           # Client tests (TODO)
    ├── test_tools.py                  # Tools tests (TODO)
    └── test_integration.py            # Integration tests (TODO)
```

---

## Testing

```bash
# Test Grist connection
cd utility-scripts
python test_grist_connection.py

# Run unit tests (TODO)
pytest -v
```

---

## Production Deployment

1. Deploy to EC2 (see [../EC2_DEPLOYMENT.md](../EC2_DEPLOYMENT.md))
2. Configure systemd service for auto-start
3. Setup Nginx reverse proxy + HTTPS
4. Configure CORS for production domains
5. Enable monitoring and logging

---

## DarcyIQ Integration

Configure in DarcyIQ:
```json
{
  "name": "Grist Data Manager",
  "url": "https://your-domain.com",
  "auth": {
    "type": "api_key",
    "token": "YOUR_MCP_AUTH_TOKEN"
  }
}
```

---

**Last Updated**: January 22, 2026
