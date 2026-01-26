#!/bin/bash
# Xavfsiz Git Pull Skripti

echo "=== Xavfsiz Git Pull ==="

cd /root/geeks_hr_bot

# 1. Status tekshirish
echo "1. Git status tekshirish..."
git status --short

# 2. Untracked fayllarni tekshirish
echo ""
echo "2. Untracked fayllar:"
UNTRACKED=$(git ls-files --others --exclude-standard)
if [ -n "$UNTRACKED" ]; then
    echo "   Untracked fayllar topildi:"
    echo "$UNTRACKED"
    
    # wsgi.py ni git'ga qo'shish
    if echo "$UNTRACKED" | grep -q "wsgi.py"; then
        echo "   wsgi.py git'ga qo'shilmoqda..."
        git add wsgi.py
        git commit -m "Add wsgi.py for Gunicorn deployment" || echo "   ⚠️  Commit qilinmadi"
    fi
    
    # Boshqa muhim fayllar
    for file in $UNTRACKED; do
        if [[ "$file" == *.py ]] || [[ "$file" == *.sh ]] || [[ "$file" == *.md ]]; then
            if [ -f "$file" ]; then
                echo "   $file git'ga qo'shilmoqda..."
                git add "$file"
                git commit -m "Add $file" || echo "   ⚠️  Commit qilinmadi"
            fi
        fi
    done
else
    echo "   ✅ Untracked fayllar yo'q"
fi

# 3. Modified fayllarni tekshirish
echo ""
echo "3. Modified fayllar:"
MODIFIED=$(git diff --name-only)
if [ -n "$MODIFIED" ]; then
    echo "   Modified fayllar topildi:"
    echo "$MODIFIED"
    
    # Backup yaratish
    echo "   Backup yaratilmoqda..."
    BACKUP_DIR="/root/geeks_hr_bot_backup_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    for file in $MODIFIED; do
        if [ -f "$file" ]; then
            cp "$file" "$BACKUP_DIR/" 2>/dev/null || true
        fi
    done
    echo "   ✅ Backup yaratildi: $BACKUP_DIR"
    
    # Stash qilish
    echo "   O'zgarishlar stash qilinmoqda..."
    git stash push -m "Backup before pull $(date +%Y%m%d_%H%M%S)" || echo "   ⚠️  Stash qilinmadi"
else
    echo "   ✅ Modified fayllar yo'q"
fi

# 4. Pull qilish
echo ""
echo "4. Git pull qilinmoqda..."
if git pull; then
    echo "   ✅ Pull muvaffaqiyatli!"
    
    # Stash'dan qaytarish (agar kerak bo'lsa)
    if [ -n "$MODIFIED" ]; then
        echo ""
        echo "5. Stash'dan qaytarish..."
        if git stash pop 2>/dev/null; then
            echo "   ✅ Stash'dan qaytarildi"
        else
            echo "   ⚠️  Stash conflict bor yoki stash bo'sh"
            echo "   Backup: $BACKUP_DIR"
        fi
    fi
else
    echo "   ❌ Pull xatolik!"
    if [ -n "$BACKUP_DIR" ]; then
        echo "   Backup: $BACKUP_DIR"
    fi
    exit 1
fi

# 6. Service restart (agar kerak bo'lsa)
echo ""
echo "6. Service restart qilinmoqda..."
sudo systemctl restart hrbot 2>/dev/null || echo "   ⚠️  Service restart qilinmadi"
sleep 2
sudo systemctl status hrbot --no-pager -l | head -5 2>/dev/null || echo "   ⚠️  Service status ko'rinmadi"

echo ""
echo "✅ Tugadi!"
