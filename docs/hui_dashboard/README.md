# Hui PWA Dashboard

Local-first PWA dashboard for U.S. equities with a dedicated quant-score board.

Last updated: 2026-02-18

## Product snapshot

- Multi-language UI (10 languages): `zh/en/es/fr/de/ja/ko/pt/it/ru`
- Theme toggle: `Dawn` (light) / `Nocturne` (dark), remembers user preference
- Signal leaderboard with filters + sort + favorites
- Symbol lookup (jump to `/symbol/<TICKER>`)
- Research panel with tabbed layout (`Factors / Combo / Process / System`) to avoid long-scroll overload
- Strategy/backtest technical detail panels (collapsed by default)
- Sample placeholder images in "coming soon" blocks
- Daily visitor stats (UV/PV), anonymous, shown in footer
- Official risk disclaimer in footer

## Data + API

- Primary data source: `QUANT_SCORE_ROOT` (default `/Users/hui/quant_score/v4`)
- Main API endpoint: `/api/quant/scoreboard`
- Research context endpoint: `/api/quant/research_context`
- Symbol snapshot endpoint: `/api/quant/symbol/{symbol}`
- Outputs:
  - `top`, `bottom` signal lists
  - `strategies` and `strategy_history`
  - `data_status`, `recent_runs`
  - `visitors` (daily UV/PV)

## Quant research board (latest sync)

The "研究与系统细节" panel now reads current V4 combo research context directly:
- Locked core combo: `linear`, `value=0.90`, `momentum=0.10`
- Layer2 fixed train/test (official locked run): `train_ic=0.080637`, `test_ic=0.053038`
- Layer3 walk-forward (2013-2025): `test_ic mean=0.057578`, `test_ic_overall mean=0.050814`
- Stage2 filter details and system architecture modules are rendered dynamically from V4 config/docs.

If local result files are not synced yet, the board falls back to `STATUS.md` official metrics to avoid showing stale values.

First live trading-day snapshot archive:
- Trading day: `2026-02-18` (using signal date `2026-02-17`)
- Local archive:
  - `/Users/hui/quant_score/v4/live_snapshots/trade_2026-02-18_from_signal_2026-02-17/`
- Web-side archive:
  - `/home/ubuntu/Hui/data/quant_score/v4/live_snapshots/trade_2026-02-18_from_signal_2026-02-17/`

## Lightweight server mode (recommended)

For small OCI instances, use minimal daily uploads:
- `strategies/combo_v2/results/test_signals_latest.csv`
- latest `strategies/combo_v2/runs/*.json` (keep last 1-3)
- `strategies/combo_v2/config.py`
- `STATUS.md`
- `COMBO_WEIGHT_EXPERIMENTS.md`

Optional periodic uploads:
- latest `walk_forward_summary.csv` (final/stress)
- latest combo `segment_summary.csv`

New runtime knobs (`.env`):
- `STRATEGY_HISTORY_LIMIT` (default `6`)
- `API_CACHE_TTL_SECONDS` (default `30`)

These reduce payload and repeated disk scans in API handlers.

## Visitor tracking (compliant)

Anonymous daily UV/PV is tracked server-side:
- Cookie key: `hv` (random UUID, no IP stored)
- Storage: `data/visitors_daily.json`
- Rolling retention: 60 days
- Display: footer "Today UV / PV"

Files:
- `app/visitor_store.py` (storage + counters)
- `app/main.py` (middleware + API payload)

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# optional
cp .env.example .env

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`.

## Daily/Periodic data sync scripts

Scripts:
- `scripts/sync_daily_min.sh`: daily minimal sync to OCI
- `scripts/sync_research_snapshot.sh`: on-demand sync including research snapshots

Examples:
```bash
# dry-run first
DRY_RUN=1 ./scripts/sync_daily_min.sh

# daily sync
./scripts/sync_daily_min.sh

# periodic research sync
./scripts/sync_research_snapshot.sh
```

Common env overrides:
- `REMOTE_USER`, `REMOTE_HOST`, `REMOTE_QUANT_ROOT`
- `SSH_KEY=/path/to/key`
- `RUNS_TO_PUSH=3`

## Notes
- Quant signals are loaded from `QUANT_SCORE_ROOT` (default: `/Users/hui/quant_score/v4`).
- The quant board reads the latest `*_signals_latest.csv` files and the latest run JSON per strategy.

## UI/UX behaviors

- Language:
  - Defaults to browser language if supported; otherwise English
  - Language choice is persisted in `localStorage`
  - New research-panel keys are fully translated for `zh/en`; other enabled languages currently fall back to English for these keys
- Theme:
  - Default: `Dawn` (light)
  - User choice persisted in `localStorage`
- Search fields:
  - Symbol search does **not** persist on refresh
  - Filter sort **does** persist

## Performance optimizations

- Table rendering is paged (virtualized by page):
  - First page renders immediately
  - Additional rows load on scroll
- Non-critical sections render during idle time
- Diff-based re-rendering to avoid unnecessary DOM updates
- `content-visibility: auto` on cards to skip offscreen paint

## PWA / cache notes

Service worker cache name is versioned:
- See `app/static/sw.js` for `CACHE_NAME`
- When updating UI, bump `CACHE_NAME` to force refresh

## Oracle Cloud deployment (Hui VCN, public-subnet)

This is the working production setup on OCI (Ubuntu 22.04, VM.Standard.E2.1.Micro).

### 1) VCN + subnet + routing

- Create VCN `Hui` (10.0.0.0/16).
- Create Internet Gateway `Hui-igw`.
- Create Public Subnet `public-subnet` (10.0.1.0/24, public).
- Route table (Default Route Table for Hui):
  - `0.0.0.0/0 -> Hui-igw`
- Security list:
  - Ingress TCP 8000, 80, 443 from `0.0.0.0/0`

### 2) Instance

- Image: Ubuntu 22.04 (x86_64)
- Shape: VM.Standard.E2.1.Micro
- VCN: `Hui`
- Subnet: `public-subnet`
- Public IPv4: **Yes**

Current instance public IP: `132.226.88.196`

### 3) Deploy app

```bash
rsync -av --delete --exclude .venv --exclude __pycache__ --exclude .DS_Store --exclude data \
  "/Users/hui/Hui/" -e "ssh -i '/Users/hui/Downloads/ssh-key-2026-02-03 (3).key'" \
  ubuntu@132.226.88.196:~/Hui/

ssh -i "/Users/hui/Downloads/ssh-key-2026-02-03 (3).key" ubuntu@132.226.88.196
cd ~/Hui
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Restart service:
```bash
sudo systemctl restart hui-uvicorn
```

### 4) systemd (auto-restart)

```bash
sudo tee /etc/systemd/system/hui-uvicorn.service >/dev/null <<'EOF'
[Unit]
Description=Hui FastAPI Uvicorn
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/Hui
Environment="PATH=/home/ubuntu/Hui/.venv/bin"
ExecStart=/home/ubuntu/Hui/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable hui-uvicorn
sudo systemctl restart hui-uvicorn
```

### 5) Firewall (instance)

```bash
sudo iptables -I INPUT 1 -p tcp --dport 8000 -j ACCEPT
sudo iptables -I INPUT 1 -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT 1 -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save
```

### 6) Domain + HTTPS (Cloudflare + Nginx + Certbot)

Domain: `whalpha.com` (DNS-only on Cloudflare)

DNS records:
- `A @ -> 132.226.88.196` (DNS only)
- `CNAME www -> @` (DNS only)

Nginx + Certbot:

```bash
sudo apt install -y nginx certbot python3-certbot-nginx

sudo tee /etc/nginx/sites-available/whalpha.com >/dev/null <<'EOF'
server {
    listen 80;
    server_name whalpha.com www.whalpha.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/whalpha.com /etc/nginx/sites-enabled/whalpha.com
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

sudo certbot --nginx -d whalpha.com -d www.whalpha.com \
  --non-interactive --agree-tos -m wanghui6666666@gmail.com --redirect
```

Access:
- https://whalpha.com
- https://www.whalpha.com

## Production URLs (current)

- Public IP: `132.226.88.196`
- Domain: `whalpha.com`
- HTTPS: `https://whalpha.com` and `https://www.whalpha.com`

## DNS (Cloudflare)

Records (DNS only / gray cloud):
- `A @ -> 132.226.88.196`
- `CNAME www -> @`

## Notes

- App runs under systemd: `hui-uvicorn`
- Nginx proxies 80/443 to `127.0.0.1:8000`
- Instance firewall allows 8000/80/443 (iptables + netfilter-persistent)

## Troubleshooting

### Service won't start (port in use)
```bash
sudo lsof -iTCP:8000 -sTCP:LISTEN -n -P
sudo kill <PID>
sudo systemctl reset-failed hui-uvicorn
sudo systemctl restart hui-uvicorn
```

### Service worker showing old UI
- Hard reload: `Cmd+Shift+R`
- Or unregister SW: DevTools → Application → Service Workers → Unregister

## Known UI notes

- Native select arrow styling differs across browsers; custom arrows are used on language switch.
- Some mobile browsers may still vary in select arrow rendering; check after major CSS changes.

## Background services (macOS launchd)

If you want the app and Cloudflare Quick Tunnel to run in the background (no iTerm windows), use macOS `launchd`.

### Create LaunchAgents

```bash
mkdir -p ~/Library/LaunchAgents

cat > ~/Library/LaunchAgents/com.hui.uvicorn.plist <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key><string>com.hui.uvicorn</string>
    <key>ProgramArguments</key>
    <array>
      <string>/Users/hui/Hui/.venv/bin/python</string>
      <string>-m</string>
      <string>uvicorn</string>
      <string>app.main:app</string>
      <string>--host</string><string>0.0.0.0</string>
      <string>--port</string><string>8000</string>
    </array>
    <key>WorkingDirectory</key><string>/Users/hui/Hui</string>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>StandardOutPath</key><string>/tmp/uvicorn.log</string>
    <key>StandardErrorPath</key><string>/tmp/uvicorn.err</string>
  </dict>
</plist>
PLIST

cat > ~/Library/LaunchAgents/com.hui.cloudflared.plist <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key><string>com.hui.cloudflared</string>
    <key>ProgramArguments</key>
    <array>
      <string>/opt/homebrew/bin/cloudflared</string>
      <string>tunnel</string>
      <string>--url</string><string>http://localhost:8000</string>
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>StandardOutPath</key><string>/tmp/cloudflared.log</string>
    <key>StandardErrorPath</key><string>/tmp/cloudflared.err</string>
  </dict>
</plist>
PLIST
```

### Start services

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.hui.uvicorn.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.hui.cloudflared.plist
```

### Check logs

```bash
tail -n 50 /tmp/uvicorn.log
tail -n 50 /tmp/cloudflared.log
```

### Check status

```bash
launchctl print gui/$(id -u)/com.hui.uvicorn
launchctl print gui/$(id -u)/com.hui.cloudflared
```

### Stop services

```bash
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.hui.uvicorn.plist
launchctl bootout gui/$(id -u) ~/Library/LaunchAgents/com.hui.cloudflared.plist
```
