# HR Bot - Gunicorn Deployment Guide

## Server Requirements

- Python 3.7+
- Gunicorn
- Nginx
- Systemd

## Step 1: Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and dependencies
sudo apt install python3 python3-pip python3-venv -y

# Install Nginx
sudo apt install nginx -y
```

## Step 2: Clone/Upload Bot Code

```bash
# Navigate to project directory
cd /root/geeks_hr_bot

# Or if cloning from git:
# git clone <repository-url> /root/geeks_hr_bot
# cd /root/geeks_hr_bot
```

## Step 3: Create Virtual Environment

```bash
cd /root/geeks_hr_bot
python3 -m venv .venv
source .venv/bin/activate
```

## Step 4: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

## Step 5: Configure Environment Variables

```bash
nano .env
```

Add the following:

```env
BOT_TOKEN=8423618425:AAFvaOokkQc5qk5ejmyiiW1aTinoTZK1uyE
ADMIN_ID=668618297
GROUP_ID=-4946035687
SESSION_TIMEOUT=3600
WEBHOOK_MODE=true
WEBHOOK_SECRET=optional_secret_token
```

## Step 6: Initialize Database

```bash
python init_db.py
```

## Step 7: Create Logs Directory

```bash
mkdir -p logs
chmod 755 logs
```

## Step 8: Set Permissions

```bash
chown -R www-data:www-data /root/geeks_hr_bot
chmod 755 /root/geeks_hr_bot
chmod 644 /root/geeks_hr_bot/*.py
chmod 644 /root/geeks_hr_bot/.env
```

## Step 9: Create Systemd Service

```bash
# Copy service file
sudo cp systemd/hrbot.service /etc/systemd/system/

# Edit if needed (check paths)
sudo nano /etc/systemd/system/hrbot.service

# Reload systemd
sudo systemctl daemon-reload

# Enable and start service
sudo systemctl enable hrbot
sudo systemctl start hrbot

# Check status
sudo systemctl status hrbot
```

## Step 10: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/hrbot
```

Add the following configuration:

```nginx
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name hrbot.geeksandijan.uz;
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name hrbot.geeksandijan.uz;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/hrbot.geeksandijan.uz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hrbot.geeksandijan.uz/privkey.pem;
    
    # SSL optimization
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Webhook endpoint - token pattern
    location ~ ^/[0-9]+:[A-Za-z0-9_-]+$ {
        proxy_pass http://127.0.0.1:8004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Webhook specific settings
        proxy_method POST;
        proxy_request_buffering off;
        client_max_body_size 1M;
        
        # Timeouts
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Other endpoints (health, setwebhook, etc.)
    location / {
        proxy_pass http://127.0.0.1:8004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/hrbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## Step 11: Set Up SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d hrbot.geeksandijan.uz
```

## Step 12: Set Webhook

```bash
cd /root/geeks_hr_bot
source .venv/bin/activate

# Get bot token from .env
BOT_TOKEN=$(grep "^BOT_TOKEN=" .env | cut -d'=' -f2)

# Set webhook
python setup_webhook.py "https://hrbot.geeksandijan.uz/${BOT_TOKEN}"

# Or manually:
# python -c "
# import requests
# import os
# from dotenv import load_dotenv
# load_dotenv()
# token = os.getenv('BOT_TOKEN')
# url = f'https://api.telegram.org/bot{token}/setWebhook'
# data = {'url': f'https://hrbot.geeksandijan.uz/{token}'}
# r = requests.post(url, json=data)
# print(r.json())
# "
```

## Step 13: Verify Deployment

```bash
# 1. Check service status
sudo systemctl status hrbot

# 2. Check logs
sudo journalctl -u hrbot -n 50 --no-pager
tail -n 50 /root/geeks_hr_bot/logs/error.log

# 3. Test health endpoint
curl https://hrbot.geeksandijan.uz/health

# 4. Check webhook info
curl https://hrbot.geeksandijan.uz/webhookinfo

# 5. Test bot in Telegram
# Send /start to your bot
```

## Troubleshooting

### Bot not responding

1. Check service status:
   ```bash
   sudo systemctl status hrbot
   ```

2. Check logs:
   ```bash
   sudo journalctl -u hrbot -f
   tail -f /root/geeks_hr_bot/logs/error.log
   ```

3. Check webhook:
   ```bash
   curl https://hrbot.geeksandijan.uz/webhookinfo
   ```

4. Test webhook manually:
   ```bash
   BOT_TOKEN=$(grep "^BOT_TOKEN=" .env | cut -d'=' -f2)
   curl -X POST "https://hrbot.geeksandijan.uz/${BOT_TOKEN}" \
        -H "Content-Type: application/json" \
        -d '{"update_id":999999999,"message":{"message_id":1,"from":{"id":123456789},"chat":{"id":123456789},"date":1234567890,"text":"/start"}}'
   ```

### Service won't start

1. Check permissions:
   ```bash
   ls -la /root/geeks_hr_bot
   chown -R www-data:www-data /root/geeks_hr_bot
   ```

2. Check .env file:
   ```bash
   cat .env
   ```

3. Test Gunicorn manually:
   ```bash
   cd /root/geeks_hr_bot
   source .venv/bin/activate
   gunicorn --bind 127.0.0.1:8004 wsgi:application
   ```

### Nginx errors

1. Check Nginx config:
   ```bash
   sudo nginx -t
   ```

2. Check Nginx logs:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. Check if port 8004 is listening:
   ```bash
   netstat -tuln | grep 8004
   ```

## Maintenance

### Restart service

```bash
sudo systemctl restart hrbot
```

### View logs

```bash
# Service logs
sudo journalctl -u hrbot -f

# Application logs
tail -f /root/geeks_hr_bot/logs/error.log
tail -f /root/geeks_hr_bot/logs/access.log
```

### Update bot code

```bash
cd /root/geeks_hr_bot
git pull  # if using git
# or upload new files

# Restart service
sudo systemctl restart hrbot
```

### Backup database

```bash
cp /root/geeks_hr_bot/hr_bot.db /backup/hr_bot_$(date +%Y%m%d).db
```
