# Grist with SQLite - EC2 Deployment

Self-hosted Grist spreadsheet/database platform using SQLite for data storage, containerized with Docker, ready for AWS EC2 deployment.

---

## What is Grist?

Grist is a modern, open-source spreadsheet-database hybrid that combines the flexibility of spreadsheets with the power of databases. It's perfect for:
- Building custom applications without code
- Managing structured data with relationships
- Creating forms and dashboards
- API-driven data workflows
- Collaborative team workspaces

---

## Architecture

This deployment uses:
- **Grist**: Latest stable version from Docker Hub
- **SQLite**: Default embedded database (no external DB needed)
- **Docker Compose**: Container orchestration
- **Persistent Volumes**: Data stored in local `./persist` directory

### Data Storage

SQLite databases created in `/persist` directory:
- `home.sqlite3` - Users, workspaces, and document metadata
- `grist-sessions.db` - Browser session data
- `docs/*.grist` - Individual Grist documents (also SQLite files)

---

## Features

- **Zero Database Setup**: SQLite works out-of-the-box, no PostgreSQL/MySQL needed
- **Easy Deployment**: Single `docker compose up` command
- **Persistent Storage**: All data survives container restarts
- **Portable**: Backup/restore by copying `persist/` directory
- **Scalable**: Upgrade to PostgreSQL later if needed
- **Secure**: Session secrets, single-port mode, optional HTTPS
- **MCP Server**: Model Context Protocol server for AI assistant integration (see [MCP_SERVER.md](MCP_SERVER.md))

---

## Prerequisites

- AWS EC2 instance (Ubuntu 22.04 LTS recommended)
- Docker and Docker Compose installed
- Ports open: 22 (SSH), 80/443 (HTTP/HTTPS)
- For hardened deployments, keep `8484` closed publicly and route only through Nginx.

---

## Quick Start (Local Development)

### 1. Clone Repository
```bash
git clone <your-repo-url>
cd grist-sqlite-ec2
```

### 2. Create Environment File
```bash
cp .env.example .env
```

### 3. Generate Session Secret
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Edit .env
```bash
nano .env
```

Set required values:
```bash
GRIST_SESSION_SECRET=<generated_secret>
GRIST_DEFAULT_EMAIL=your-email@example.com
GRIST_DOMAIN=localhost
PORT=8484
```

### 5. Start Grist
```bash
docker compose up -d
```

### 6. Access Grist
Open browser: `http://localhost:8484`

---

## EC2 Deployment

See **[EC2_DEPLOYMENT.md](EC2_DEPLOYMENT.md)** for complete step-by-step guide including:
- EC2 instance setup
- Docker installation
- Security configuration
- Custom domain & HTTPS
- Automated backups
- Production checklist

Quick EC2 deployment:
```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@your-ec2-ip

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker ubuntu
newgrp docker

# Clone and setup
git clone <your-repo-url> grist-sqlite-ec2
cd grist-sqlite-ec2
cp .env.example .env
nano .env  # Configure values

# Start Grist
docker compose up -d

# Access
https://your-domain
```

---

## Configuration

### Environment Variables

#### Required
- `GRIST_SESSION_SECRET` - Secret key for session management (generate with Python script)
- `GRIST_DEFAULT_EMAIL` - Email for initial admin account

#### Optional
- `PORT` - Server port (default: 8484)
- `GRIST_DOMAIN` - Domain name or IP address
- `GRIST_SANDBOX_FLAVOR` - Plugin sandbox security (gvisor, unsandboxed, pyodide)

See `.env.example` for full configuration options.

---

## Usage

### Basic Operations

#### Start Grist
```bash
docker compose up -d
```

#### Stop Grist
```bash
docker compose down
```

#### Restart Grist
```bash
docker compose restart
```

#### View Logs
```bash
docker compose logs -f
```

#### Check Status
```bash
docker compose ps
```

### User Management

1. First user (using `GRIST_DEFAULT_EMAIL`) becomes admin automatically
2. Admin can invite users via Grist UI
3. Users create accounts via invite links

### Data Management

#### Backup Data
```bash
# Backup entire persist directory
tar -czf grist-backup-$(date +%Y%m%d).tar.gz ./persist

# Or copy SQLite files directly
cp -r ./persist ~/grist-backup
```

#### Restore Data
```bash
# Stop Grist
docker compose down

# Restore files
tar -xzf grist-backup-YYYYMMDD.tar.gz

# Start Grist
docker compose up -d
```

#### Check Database Size
```bash
du -sh ./persist
```

---

## Docker Commands

### Update Grist to Latest Version
```bash
docker compose pull
docker compose up -d
```

### View Container Details
```bash
docker inspect grist-app
```

### Execute Commands in Container
```bash
docker exec -it grist-app bash
```

### Clean Up Old Images
```bash
docker system prune -a
```

---

## Troubleshooting

### Container Won't Start

**Check logs:**
```bash
docker compose logs
```

**Common issues:**
- Missing `.env` file → Create from `.env.example`
- Port 8484 already in use → Change `PORT` in `.env`
- Permission errors → Run `chmod -R 755 ./persist`

### Can't Access Grist

**From EC2:**
```bash
curl http://localhost:8484
```

**If works locally but not remotely:**
- Check EC2 Security Group allows ports 80/443
- Check firewall: `sudo ufw status`
- Verify `GRIST_DOMAIN` matches your access URL

### Database Errors

**Check SQLite integrity:**
```bash
sqlite3 ./persist/home.sqlite3 "PRAGMA integrity_check;"
```

**Reset database (WARNING: deletes all data):**
```bash
docker compose down
rm -rf ./persist/*
docker compose up -d
```

### Performance Issues

**Check system resources:**
```bash
docker stats grist-app
```

**Upgrade instance type or optimize:**
- Use t3.small or larger for production
- Monitor disk I/O with `iostat`
- Consider PostgreSQL for high-load scenarios

---

## Security

### Session Secret
- **ALWAYS** generate a strong random secret
- Never commit `.env` to version control
- Rotate secrets periodically

### Firewall Configuration
```bash
sudo ufw allow 22/tcp    # SSH only
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### HTTPS Setup
- Use Nginx as reverse proxy
- Install Let's Encrypt SSL certificate
- Redirect HTTP to HTTPS
- See **EC2_DEPLOYMENT.md** for detailed setup

### File Permissions
```bash
chmod 600 .env                    # Only owner can read/write
chmod -R 755 ./persist            # Container can read/write data
```

---

## Production Recommendations

1. **Use HTTPS**: Always encrypt traffic in production
2. **Regular Backups**: Automate daily backups to S3 or external storage
3. **Monitor Logs**: Set up log aggregation (CloudWatch, ELK stack)
4. **Resource Monitoring**: Track CPU, memory, disk usage
5. **Update Regularly**: Keep Grist and Docker images up-to-date
6. **Restrict Access**: Use security groups to limit incoming traffic
7. **Test Restores**: Verify backup integrity regularly

---

## Upgrading to PostgreSQL (Optional)

If you outgrow SQLite, migrate to PostgreSQL:

1. Export Grist data
2. Set up PostgreSQL (RDS or self-hosted)
3. Update `docker-compose.yml` with PostgreSQL connection
4. Restart Grist and import data

See Grist documentation for migration guides.

---

## Project Structure

```
grist-sqlite-ec2/
├── docker-compose.yml      # Docker Compose configuration
├── .env.example            # Environment template
├── .env                    # Environment configuration (gitignored)
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── MCP_SERVER.md           # MCP server documentation
├── EC2_DEPLOYMENT.md       # Detailed EC2 setup guide
├── persist/                # Persistent data directory (gitignored)
│   ├── home.sqlite3        # Users, workspaces, docs metadata
│   ├── grist-sessions.db   # Session data
│   └── docs/               # Individual .grist files
└── mcp-server/             # MCP server for AI assistant integration
    ├── server.py           # FastAPI MCP server
    ├── grist_client.py     # Grist REST API client
    ├── tools.py            # MCP tools for Grist operations
    ├── requirements.txt    # Python dependencies
    ├── .env.example        # MCP server environment template
    ├── .gitignore          # Git ignore rules
    └── tests/              # Test suite
        ├── test_grist_client.py
        ├── test_tools.py
        └── test_integration.py
```

---

## MCP Server Integration

This deployment includes a Model Context Protocol (MCP) server that allows AI assistants (like DarcyIQ) to:
- List tables in Grist documents
- Read and query record data
- Create new records
- Update existing records
- Delete records
- Automate data workflows via natural language

See **[MCP_SERVER.md](MCP_SERVER.md)** for complete setup and integration guide.

**Quick MCP Setup:**
```bash
cd mcp-server
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Configure Grist API key and MCP auth token in .env
python server.py
```

The MCP server connects to your Grist instance via REST API and provides a JSON-RPC 2.0 interface compatible with DarcyIQ and other AI assistants.

---

## Resources

### Documentation
- **Grist Docs**: https://support.getgrist.com/
- **Self-Managed Guide**: https://support.getgrist.com/self-managed/
- **API Documentation**: https://support.getgrist.com/api/

### Docker
- **Docker Hub**: https://hub.docker.com/r/gristlabs/grist
- **GitHub**: https://github.com/gristlabs/grist-core

### Community
- **Forum**: https://community.getgrist.com/
- **Discord**: https://discord.gg/MYKpYQ3fbP

---

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Test changes locally
4. Submit a pull request

---

## License

[Your License Here]

---

## Support

- **Issues**: Check troubleshooting section above
- **EC2 Setup**: See [EC2_DEPLOYMENT.md](EC2_DEPLOYMENT.md)
- **Grist Help**: Visit https://support.getgrist.com/

---

## Quick Reference Card

### First Time Setup
```bash
cp .env.example .env
nano .env  # Set GRIST_SESSION_SECRET and GRIST_DEFAULT_EMAIL
docker compose up -d
```

### Daily Operations
```bash
docker compose ps          # Check status
docker compose logs -f     # View logs
docker compose restart     # Restart
```

### Backup & Restore
```bash
# Backup
tar -czf backup.tar.gz ./persist

# Restore
docker compose down
tar -xzf backup.tar.gz
docker compose up -d
```

### Updates
```bash
docker compose pull
docker compose up -d
```

---

**Created**: January 22, 2026
**Status**: Ready for deployment
