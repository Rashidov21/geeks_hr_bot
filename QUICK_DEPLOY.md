# HR Bot - Tezkor Deployment (VPS)

## 1. Serverda bot kodini yuklash

```bash
# Bot kodini /root/geeks_hr_bot papkasiga yuklang
cd /root/geeks_hr_bot
```

## 2. Virtual environment va dependencies

```bash
# Virtual environment yaratish
python3 -m venv .venv
source .venv/bin/activate

# Dependencies o'rnatish
pip install --upgrade pip
pip install -r requirements.txt
```

## 3. .env faylini sozlash

```bash
nano .env
```

Quyidagilarni qo'shing:

```env
BOT_TOKEN=8423618425:AAFvaOokkQc5qk5ejmyiiW1aTinoTZK1uyE
ADMIN_ID=668618297
GROUP_ID=-4946035687
SESSION_TIMEOUT=3600
WEBHOOK_MODE=true
```

## 4. Database yaratish

```bash
python init_db.py
```

## 5. Logs papkasi

```bash
mkdir -p logs
chmod 755 logs
```

## 6. Permissions

```bash
chown -R www-data:www-data /root/geeks_hr_bot
chmod 755 /root/geeks_hr_bot
```

## 7. Systemd Service

```bash
# Service faylini ko'chirish
sudo cp systemd/hrbot.service /etc/systemd/system/

# Service faylini tahrirlash (path'larni tekshirish)
sudo nano /etc/systemd/system/hrbot.service

# Systemd reload
sudo systemctl daemon-reload

# Service'ni ishga tushirish
sudo systemctl enable hrbot
sudo systemctl start hrbot

# Status tekshirish
sudo systemctl status hrbot
```

## 8. Nginx Konfiguratsiyasi

```bash
sudo nano /etc/nginx/sites-available/hrbot
```

Quyidagilarni qo'shing:

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
    
    ssl_certificate /etc/letsencrypt/live/hrbot.geeksandijan.uz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/hrbot.geeksandijan.uz/privkey.pem;
    
    # Webhook endpoint (token pattern)
    location ~ ^/[0-9]+:[A-Za-z0-9_-]+$ {
        proxy_pass http://127.0.0.1:8004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_method POST;
        proxy_request_buffering off;
        client_max_body_size 1M;
        
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }
    
    # Other endpoints
    location / {
        proxy_pass http://127.0.0.1:8004;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable qilish:

```bash
sudo ln -s /etc/nginx/sites-available/hrbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## 9. Webhook sozlash

```bash
cd /root/geeks_hr_bot
source .venv/bin/activate

# Bot token olish
BOT_TOKEN=$(grep "^BOT_TOKEN=" .env | cut -d'=' -f2)

# Webhook sozlash
python setup_webhook.py "https://hrbot.geeksandijan.uz/${BOT_TOKEN}"

# Yoki qo'lda:
python -c "
import requests
import os
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('BOT_TOKEN')
url = f'https://api.telegram.org/bot{token}/setWebhook'
data = {'url': f'https://hrbot.geeksandijan.uz/{token}'}
r = requests.post(url, json=data)
print(r.json())
"
```

## 10. Tekshirish

```bash
# Service status
sudo systemctl status hrbot

# Logs
sudo journalctl -u hrbot -n 50
tail -n 50 logs/error.log

# Health check
curl https://hrbot.geeksandijan.uz/health

# Webhook info
curl https://hrbot.geeksandijan.uz/webhookinfo
```

## Tezkor Buyruqlar (Bitta qator)

```bash
cd /root/geeks_hr_bot && \
python3 -m venv .venv && \
source .venv/bin/activate && \
pip install --upgrade pip && \
pip install -r requirements.txt && \
python init_db.py && \
mkdir -p logs && \
chown -R www-data:www-data . && \
sudo cp systemd/hrbot.service /etc/systemd/system/ && \
sudo systemctl daemon-reload && \
sudo systemctl enable hrbot && \
sudo systemctl start hrbot && \
echo "✅ Deployment tugadi!"
```
