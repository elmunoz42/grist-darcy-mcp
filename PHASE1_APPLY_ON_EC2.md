# Phase 1 Apply Steps (EC2)

## 1) Pull latest config
```bash
cd ~/grist-sqlite-ec2
git pull
```

## 2) Restart Grist with loopback-only bind
```bash
cd ~/grist-sqlite-ec2
docker compose up -d
docker compose ps
```

Expected port mapping should show `127.0.0.1:8484->8484/tcp` (not `0.0.0.0`).

## 3) Create basic-auth credentials for web UI
```bash
sudo apt-get update
sudo apt-get install -y apache2-utils
sudo htpasswd -c /etc/nginx/.htpasswd-grist demoadmin
```

## 4) Install Nginx site config and reload
```bash
sudo cp ~/grist-sqlite-ec2/nginx-grist-config /etc/nginx/sites-available/grist
sudo ln -sf /etc/nginx/sites-available/grist /etc/nginx/sites-enabled/grist
sudo nginx -t
sudo systemctl reload nginx
```

## 5) Close direct Grist port on host firewall
```bash
sudo ufw delete allow 8484/tcp || true
sudo ufw deny 8484/tcp
sudo ufw status
```

## 6) Close direct Grist port in AWS Security Group
- Remove inbound rule: TCP `8484` from `0.0.0.0/0` (and `::/0` if present).
- Keep only `22`, `80`, `443` as needed.

## 7) Validate
```bash
# Should return 401 Unauthorized
curl -I https://<your-domain>/

# Should still answer locally on loopback
curl -I http://127.0.0.1:8484/

# MCP path should not basic-auth challenge (still requires MCP token at app layer)
curl -I https://<your-domain>/mcp
```
