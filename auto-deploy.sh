#!/bin/bash
# Avtomatik Deployment Skripti

echo "=== Avtomatik Deployment ==="

cd /root/geeks_hr_bot

# 1. Git pull (xavfsiz)
echo "1. Git pull..."
git add -A 2>/dev/null
git commit -m "Auto commit before pull $(date +%Y%m%d_%H%M%S)" 2>/dev/null || true
git stash 2>/dev/null || true

if git pull; then
    echo "   ✅ Pull muvaffaqiyatli"
    git stash pop 2>/dev/null || true
else
    echo "   ❌ Pull xatolik!"
    git stash pop 2>/dev/null || true
    exit 1
fi

# 2. Dependencies
echo ""
echo "2. Dependencies tekshirish..."
if [ -d ".venv" ]; then
    source .venv/bin/activate
    pip install -r requirements.txt --quiet 2>/dev/null || pip install -r requirements.txt
else
    echo "   ⚠️  Virtual environment topilmadi"
fi

# 3. Database
echo ""
echo "3. Database tekshirish..."
python init_db.py 2>/dev/null || echo "   ⚠️  Database init qilinmadi"

# 4. Permissions
echo ""
echo "4. Permissions tuzatish..."
chown -R www-data:www-data . 2>/dev/null || echo "   ⚠️  Permissions o'zgartirilmadi"
chmod 755 . 2>/dev/null || true

# 5. Service restart
echo ""
echo "5. Service restart..."
sudo systemctl restart hrbot 2>/dev/null || echo "   ⚠️  Service restart qilinmadi"
sleep 3

# 6. Status tekshirish
echo ""
echo "6. Status tekshirish..."
if sudo systemctl is-active --quiet hrbot 2>/dev/null; then
    echo "   ✅ Service ishlayapti"
else
    echo "   ❌ Service ishlamayapti!"
    sudo systemctl status hrbot --no-pager -l | head -10 2>/dev/null || true
    exit 1
fi

echo ""
echo "✅ Deployment tugadi!"
