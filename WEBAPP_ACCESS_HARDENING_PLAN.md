# Grist Webapp Access Hardening Plan (EC2 Demo)

## Goal
Prevent direct browser access to the Grist web UI while keeping MCP/API connectivity working for agent use.

## Current State (repo + deployment)
- `docker-compose.yml` already sets:
  - `GRIST_FORCE_LOGIN=true`
  - `GRIST_ANON_PLAYGROUND=false`
- Grist is exposed on host port `8484` via `ports: "${PORT:-8484}:8484"`.
- Nginx proxies `/` to Grist and `/mcp` to MCP, but no web auth is configured in `nginx-grist-config`.
- Existing deployment docs still suggest opening port `8484` publicly in AWS Security Group/UFW.

## What Grist Docs Say (self-managed)
- For production access control, use reverse proxy + login flow and force login.
- Grist supports proxy-provided identity headers using:
  - `GRIST_FORWARD_AUTH_HEADER`
  - `GRIST_FORWARD_AUTH_LOGIN`
  - `GRIST_FORWARD_AUTH_LOGOUT_PATH`
  - `GRIST_IGNORE_SESSION=true`
- For single-organization setup, docs also call out:
  - `GRIST_HOSTED=true`
  - `GRIST_SINGLE_ORG=<org>`
  - `GRIST_DEFAULT_EMAIL=<admin email>`
  - `APP_HOME_URL=<public url>`

Reference: https://support.getgrist.com/self-managed/#the-essentials

## Recommended Approach (Phase 1: simplest)
Use Nginx Basic Auth in front of the UI, plus network lock-down of port `8484`.

Why this first:
- Fastest path for a single-user demo environment.
- No app code changes.
- No Cognito/OAuth complexity.
- Works even if Grist internal login behavior is not fully configured.

### Phase 1 Implementation Plan
1. Stop direct public access to Grist container port.
   - AWS Security Group: remove inbound `8484` from `0.0.0.0/0`.
   - UFW: remove/deny `8484` publicly.
   - Keep access only through Nginx (`80/443`).
2. Bind Grist to localhost only.
   - Change compose mapping to `127.0.0.1:${PORT:-8484}:8484`.
3. Add HTTP Basic Auth at Nginx for `/` (web UI path).
   - Create htpasswd file with one strong username/password.
   - Add `auth_basic` directives in `location /`.
4. Keep MCP path behavior explicit.
   - Keep `/mcp` protected by MCP token auth (already implemented in `mcp-server/server.py`).
   - Optionally add IP allowlist for `/mcp` if caller IP is stable.
5. Restart and validate.
   - `curl -I https://<domain>/` should return `401` without credentials.
   - Browser should prompt for credentials before Grist loads.
   - MCP calls with valid token should still succeed.

## Optional Hardening (Phase 2: cleaner SSO)
Replace Basic Auth with Cognito/OAuth via `oauth2-proxy` and pass user identity headers to Grist.

### Phase 2 Implementation Plan
1. Deploy `oauth2-proxy` (or equivalent) behind Nginx.
2. Configure Cognito User Pool + App Client.
3. Configure Nginx `auth_request` flow to oauth2-proxy.
4. Configure Grist env for forwarded auth:
   - `GRIST_FORCE_LOGIN=true`
   - `GRIST_FORWARD_AUTH_HEADER=X-Forwarded-User`
   - `GRIST_FORWARD_AUTH_LOGIN=/oauth2/sign_in`
   - `GRIST_FORWARD_AUTH_LOGOUT_PATH=/oauth2/sign_out`
   - `GRIST_IGNORE_SESSION=true`
5. Validate login/logout and identity mapping to Grist user.

## Operational Checks
- Ensure only `80/443` are internet-facing for web.
- Ensure `.env` file permissions remain restricted (`chmod 600`).
- Keep TLS enabled in Nginx (already present in current config).
- Rotate Basic Auth password periodically (if Phase 1 retained).

## Risks and Notes
- Basic Auth is sufficient for demos, but weaker UX/security than Cognito/OAuth SSO.
- If `8484` remains public, users can bypass Nginx auth by hitting `http://<ec2-ip>:8484`.
- If MCP shares same public domain, keep `/mcp` routing and auth rules explicit to avoid accidental lockout or exposure.

## Rollout Sequence
1. Apply Security Group/UFW changes.
2. Update compose port binding and restart Grist.
3. Apply Nginx Basic Auth and reload Nginx.
4. Run validation checks (UI + MCP).
5. Update deployment docs (`EC2_DEPLOYMENT.md`) to reflect no-public-8484 pattern.
