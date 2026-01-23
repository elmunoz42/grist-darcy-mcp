# Grist EC2 Deployment Guide

Complete guide for deploying Grist with SQLite on AWS EC2 using Docker.

---

## Overview

This deployment uses:
- **Grist**: Self-hosted spreadsheet/database platform
- **SQLite**: Default database (no external database needed)
- **Docker**: Containerized deployment
- **Ubuntu 22.04**: Recommended EC2 instance OS

---

## Prerequisites

- AWS EC2 instance (t2.micro or larger)
- Ubuntu 22.04 LTS
- Security group with ports 22 (SSH), 80 (HTTP), 443 (HTTPS), cat ~/.ssh/github_deploy_key.pub (Grist) open
- SSH key pair for EC2 access
- (Optional) Domain name for custom URL

---

## Step 1: Launch EC2 Instance

### Via AWS Console

1. Go to **EC2 Dashboard** → **Launch Instance**
2. Configure:
   - **Name**: `grist-server`
   - **AMI**: Ubuntu Server 22.04 LTS
   - **Instance Type**: t2.micro (or larger for production)
   - **Key Pair**: Select or create SSH key
   - **Network**: Default VPC
3. **Security Group**:
   - SSH (22): Your IP
   - HTTP (80): 0.0.0.0/0
   - HTTPS (443): 0.0.0.0/0
   - Custom TCP (8484): 0.0.0.0/0 (or your IP for testing)
4. **Storage**: 8GB minimum, 20GB recommended
5. Click **Launch Instance**

---

## Step 2: Connect to EC2

```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

---

## Step 3: Install Docker & Docker Compose

### Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### Install Docker
```bash
# Install prerequisites
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Set up the Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group (no sudo needed)
sudo usermod -aG docker $USER

# Apply group changes (or logout/login)
newgrp docker
```

### Verify Docker Installation
```bash
docker --version
docker compose version
```

---

## Step 4: Clone or Transfer Project Files

### Option A: Using Git (Recommended)

```bash
cd ~
git clone <your-repo-url> grist-sqlite-ec2
cd grist-sqlite-ec2
```

### Option B: Manual Transfer via SCP

From your local machine:
```bash
scp -i your-key.pem -r /path/to/grist-sqlite-ec2 ubuntu@your-ec2-ip:~/
```

### Option C: Create Files Manually

```bash
mkdir -p ~/grist-sqlite-ec2
cd ~/grist-sqlite-ec2

# Create docker-compose.yml (copy from your local setup)
nano docker-compose.yml

# Create .env file (copy from .env.example)
nano .env
```

---

## Step 5: Configure Environment

### Create .env File
```bash
cd ~/grist-sqlite-ec2
cp .env.example .env
nano .env
```

### Generate Session Secret
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Edit .env with Your Values
```bash
# Required
GRIST_SESSION_SECRET=<generated_secret_from_above>
GRIST_DEFAULT_EMAIL=your-email@example.com

# Server configuration
PORT=8484
GRIST_DOMAIN=your-ec2-public-dns.compute.amazonaws.com

# Optional
GRIST_SANDBOX_FLAVOR=gvisor
```

**Important**: Replace `GRIST_DOMAIN` with:
- Your EC2 public DNS: `ec2-xx-xx-xx-xx.compute-1.amazonaws.com`
- Or your custom domain: `grist.yourdomain.com`

Save and exit: `Ctrl+X` → `Y` → `Enter`

---

## Step 6: Create Persistent Data Directory

```bash
mkdir -p ~/grist-sqlite-ec2/persist
chmod 755 ~/grist-sqlite-ec2/persist
```

This directory will store:
- `home.sqlite3` - User, workspace, and document metadata
- `grist-sessions.db` - Browser session data
- `docs/` - Individual `.grist` files (also SQLite databases)

---

## Step 7: Start Grist

```bash
cd ~/grist-sqlite-ec2
docker compose up -d
```

### Verify Container is Running
```bash
docker compose ps
```

Expected output:
```
NAME        IMAGE                    STATUS        PORTS
grist-app   gristlabs/grist:latest   Up X minutes  0.0.0.0:8484->8484/tcp
```

### Check Logs
```bash
docker compose logs -f
```

Press `Ctrl+C` to exit logs.

---

## Step 8: Configure Firewall (UFW)

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 8484/tcp  # Grist
sudo ufw enable
sudo ufw status
```

---

## Step 9: Test Grist

### From EC2 Instance
```bash
curl http://localhost:8484
```

### From Your Local Machine
```bash
curl http://your-ec2-public-ip:8484
```

### In Browser
Open: `http://your-ec2-public-ip:8484`

You should see the Grist login/signup page.

---

## Step 10: Initial Setup

1. Open Grist in browser: `http://your-ec2-public-ip:8484`
2. Create account using the email from `GRIST_DEFAULT_EMAIL`
3. You're automatically the admin user
4. Start creating documents!

---

## Optional: Setup Custom Domain & HTTPS

### Prerequisites
- Domain name pointing to your EC2 instance
- DNS A record: `grist.yourdomain.com` → `your-ec2-ip`

### Install Nginx
```bash
sudo apt install nginx -y
```

### Configure Nginx as Reverse Proxy
```bash
sudo nano /etc/nginx/sites-available/grist
```

Paste:
```nginx
server {
    listen 80;
    server_name grist.yourdomain.com;

    location / {
        proxy_pass http://localhost:8484;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # WebSocket support
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts for long-running requests
        proxy_read_timeout 300;
        proxy_connect_timeout 300;
        proxy_send_timeout 300;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/grist /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Install SSL Certificate (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d grist.yourdomain.com
```

Follow prompts. Certbot will auto-configure HTTPS.

### Update .env with Domain
```bash
nano ~/grist-sqlite-ec2/.env
```

Change:
```bash
GRIST_DOMAIN=grist.yourdomain.com
```

Restart Grist:
```bash
cd ~/grist-sqlite-ec2
docker compose down
docker compose up -d
```

Access via: `https://grist.yourdomain.com`

---

## Maintenance Commands

### View Logs
```bash
cd ~/grist-sqlite-ec2
docker compose logs -f
```

### Restart Grist
```bash
docker compose restart
```

### Stop Grist
```bash
docker compose down
```

### Start Grist
```bash
docker compose up -d
```

### Update Grist
```bash
docker compose pull
docker compose up -d
```

### Check Disk Usage
```bash
du -sh ~/grist-sqlite-ec2/persist
```

### Backup SQLite Databases
```bash
# Create backup directory
mkdir -p ~/grist-backups

# Backup all persistent data
tar -czf ~/grist-backups/grist-backup-$(date +%Y%m%d).tar.gz ~/grist-sqlite-ec2/persist
```

### Restore Backup
```bash
cd ~/grist-sqlite-ec2
docker compose down
tar -xzf ~/grist-backups/grist-backup-YYYYMMDD.tar.gz -C ~/
docker compose up -d
```

---

## Troubleshooting

### Container Won't Start
```bash
# Check logs
docker compose logs

# Check if port is in use
sudo netstat -tulpn | grep 8484

# Restart container
docker compose down
docker compose up -d
```

### Permission Errors
```bash
# Fix persist directory permissions
sudo chown -R 1000:1000 ~/grist-sqlite-ec2/persist
chmod -R 755 ~/grist-sqlite-ec2/persist
```

### Can't Access from Browser
- Verify EC2 Security Group allows port 8484
- Check UFW firewall: `sudo ufw status`
- Test locally first: `curl http://localhost:8484`

### Database Errors
```bash
# Check SQLite database files
ls -lah ~/grist-sqlite-ec2/persist/

# Verify database integrity
sqlite3 ~/grist-sqlite-ec2/persist/home.sqlite3 "PRAGMA integrity_check;"
```

### Out of Disk Space
```bash
# Check disk usage
df -h

# Clean up Docker
docker system prune -a --volumes

# Remove old container logs
docker compose down
docker compose up -d
```

---

## Security Best Practices

### Environment File Security
```bash
# Restrict .env file permissions
chmod 600 ~/grist-sqlite-ec2/.env
```

### Regular Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Grist container
docker compose pull
docker compose up -d
```

### Firewall Configuration
- Only open necessary ports
- Use security groups to restrict SSH to your IP
- Use HTTPS in production (not HTTP)

### Backup Strategy
- Regular automated backups of `/persist` directory
- Test restore procedures
- Store backups off-instance (S3, another server)

### Monitoring
```bash
# Check container health
docker compose ps

# Monitor logs for errors
docker compose logs --tail=100 -f

# Check system resources
htop
```

---

## Automated Startup (Systemd)

To ensure Grist starts automatically on server reboot:

### Create Systemd Service
```bash
sudo nano /etc/systemd/system/grist.service
```

Paste:
```ini
[Unit]
Description=Grist SQLite Docker Service
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/grist-sqlite-ec2
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
User=ubuntu

[Install]
WantedBy=multi-user.target
```

### Enable and Test
```bash
sudo systemctl daemon-reload
sudo systemctl enable grist.service
sudo systemctl start grist.service
sudo systemctl status grist.service
```

### Test Auto-start
```bash
sudo reboot
```

Wait 1-2 minutes, reconnect, and check:
```bash
docker compose ps
```

---

## Cost Optimization

### Instance Sizing
- **Development/Testing**: t2.micro (1GB RAM)
- **Small Production**: t3.small (2GB RAM)
- **Medium Production**: t3.medium (4GB RAM)

### Storage
- Start with 20GB EBS volume
- Monitor usage: `df -h`
- Expand if needed via AWS Console

### Backup to S3 (Cost-Effective)
```bash
# Install AWS CLI
sudo apt install awscli -y

# Configure credentials
aws configure

# Automated backup script
cat > ~/backup-grist.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="grist-backup-$DATE.tar.gz"
tar -czf /tmp/$BACKUP_FILE ~/grist-sqlite-ec2/persist
aws s3 cp /tmp/$BACKUP_FILE s3://your-bucket-name/grist-backups/
rm /tmp/$BACKUP_FILE
EOF

chmod +x ~/backup-grist.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /home/ubuntu/backup-grist.sh
```

---

## Production Checklist

- [ ] EC2 instance launched and accessible
- [ ] Docker and Docker Compose installed
- [ ] Project files deployed to EC2
- [ ] `.env` configured with strong session secret
- [ ] Persistent storage directory created
- [ ] Container running (`docker compose ps`)
- [ ] Firewall configured (UFW)
- [ ] Grist accessible via browser
- [ ] Initial admin account created
- [ ] (Optional) Custom domain configured
- [ ] (Optional) HTTPS/SSL certificate installed
- [ ] Systemd service configured for auto-start
- [ ] Backup strategy implemented
- [ ] Monitoring set up

---

## Quick Reference

### Important Locations
- Application: `~/grist-sqlite-ec2/`
- Configuration: `~/grist-sqlite-ec2/.env`
- Data Storage: `~/grist-sqlite-ec2/persist/`
- SQLite DBs: `~/grist-sqlite-ec2/persist/*.sqlite3`

### Essential Commands
```bash
# Service management
cd ~/grist-sqlite-ec2
docker compose ps          # Check status
docker compose logs -f     # View logs
docker compose restart     # Restart
docker compose down        # Stop
docker compose up -d       # Start

# Access Grist
http://your-ec2-ip:8484
https://grist.yourdomain.com  # If custom domain

# Health check
curl http://localhost:8484
```

---

## Next Steps

1. **Access Grist**: Open in browser and create your first document
2. **Import Data**: Use CSV/Excel import or API
3. **Configure Sharing**: Set up team workspaces
4. **Build MCP Server**: (Future) Create MCP integration for AI assistants

---

## Resources

- **Grist Documentation**: https://support.getgrist.com/
- **Self-Hosting Guide**: https://support.getgrist.com/self-managed/
- **Docker Hub**: https://hub.docker.com/r/gristlabs/grist
- **GitHub**: https://github.com/gristlabs/grist-core

---

**Last Updated**: January 22, 2026
