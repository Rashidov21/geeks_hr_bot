#!/bin/bash
# Gunicorn deployment script for HR Bot

set -e

echo "=== HR Bot Gunicorn Deployment ==="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${GREEN}1. Virtual environment tekshirish...${NC}"
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}   Virtual environment topilmadi, yaratilmoqda...${NC}"
    python3 -m venv .venv
fi

echo -e "${GREEN}2. Virtual environment aktivlashtirish...${NC}"
source .venv/bin/activate

echo -e "${GREEN}3. Dependencies o'rnatish...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${GREEN}4. .env faylini tekshirish...${NC}"
if [ ! -f ".env" ]; then
    echo -e "${RED}   ❌ .env fayli topilmadi!${NC}"
    echo "   Quyidagilarni yarating:"
    echo "   BOT_TOKEN=your_bot_token"
    echo "   ADMIN_ID=your_admin_id"
    echo "   GROUP_ID=your_group_id"
    echo "   WEBHOOK_MODE=true"
    exit 1
fi

echo -e "${GREEN}5. Database yaratish...${NC}"
python init_db.py

echo -e "${GREEN}6. Logs papkasini yaratish...${NC}"
mkdir -p logs
chmod 755 logs

echo -e "${GREEN}7. Permissions tuzatish...${NC}"
chown -R www-data:www-data . 2>/dev/null || echo "   Permissions o'zgartirilmadi (root emas)"
chmod 755 .
chmod 644 *.py *.txt 2>/dev/null || true
chmod 644 .env 2>/dev/null || true

echo -e "${GREEN}8. Gunicorn test...${NC}"
gunicorn --check-config wsgi:application || echo "   ⚠️  Gunicorn config test failed"

echo ""
echo -e "${GREEN}✅ Deployment tayyor!${NC}"
echo ""
echo -e "${YELLOW}Keyingi qadamlar:${NC}"
echo "1. Systemd service yarating:"
echo "   sudo cp systemd/hrbot.service /etc/systemd/system/"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl enable hrbot"
echo "   sudo systemctl start hrbot"
echo ""
echo "2. Nginx konfiguratsiyasini sozlang"
echo ""
echo "3. Webhook sozlang:"
echo "   python setup_webhook.py https://hrbot.geeksandijan.uz/YOUR_BOT_TOKEN"
