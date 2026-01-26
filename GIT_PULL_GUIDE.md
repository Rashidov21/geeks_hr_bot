# Git Pull Muammolarini Hal Qilish

## 1. Umumiy Muammolar va Yechimlar

### Muammo 1: Untracked files conflict

**Xatolik:**
```
error: The following untracked working tree files would be overwritten by merge:
        wsgi.py
Please move or remove them before you merge.
```

**Yechim:**

```bash
cd /root/geeks_hr_bot

# Variant 1: Faylni git'ga qo'shish (tavsiya etiladi)
git add wsgi.py
git commit -m "Add wsgi.py for Gunicorn deployment"
git pull

# Variant 2: Backup qilib o'chirish
cp wsgi.py wsgi.py.backup
rm wsgi.py
git pull
# Agar yangi wsgi.py kelmasa:
cp wsgi.py.backup wsgi.py

# Variant 3: Stash qilish
git stash push -u wsgi.py
git pull
git stash pop  # Agar kerak bo'lsa
```

### Muammo 2: Local changes conflict

**Xatolik:**
```
error: Your local changes to the following files would be overwritten by merge:
        app.py
Please commit your changes or stash them before you merge.
```

**Yechim:**

```bash
# Variant 1: Commit qilish
git add app.py
git commit -m "Update app.py with webhook improvements"
git pull

# Variant 2: Stash qilish
git stash
git pull
git stash pop  # Keyin conflict'ni hal qilish

# Variant 3: Force pull (ehtiyot bo'ling - local o'zgarishlar yo'qoladi)
git reset --hard HEAD
git pull
```

### Muammo 3: Merge conflict

**Xatolik:**
```
Auto-merging app.py
CONFLICT (content): Merge conflict in app.py
```

**Yechim:**

```bash
# 1. Conflict'ni hal qilish
nano app.py
# <<<<<<< HEAD va ======= belgilarini topib, to'g'ri kodni tanlang

# 2. Conflict hal qilingandan keyin
git add app.py
git commit -m "Resolve merge conflict in app.py"

# 3. Yoki abort qilish
git merge --abort
```

## 2. To'liq Git Pull Skripti (Xavfsiz)

```bash
#!/bin/bash
# safe-git-pull.sh

echo "=== Xavfsiz Git Pull ==="

cd /root/geeks_hr_bot

# 1. Status tekshirish
echo "1. Git status tekshirish..."
git status

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
        git commit -m "Add wsgi.py for Gunicorn deployment"
    fi
    
    # Boshqa muhim fayllar
    for file in $UNTRACKED; do
        if [[ "$file" == *.py ]] || [[ "$file" == *.sh ]] || [[ "$file" == *.md ]]; then
            echo "   $file git'ga qo'shilmoqda..."
            git add "$file"
            git commit -m "Add $file"
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
        cp "$file" "$BACKUP_DIR/" 2>/dev/null || true
    done
    echo "   ✅ Backup yaratildi: $BACKUP_DIR"
    
    # Stash qilish
    echo "   O'zgarishlar stash qilinmoqda..."
    git stash push -m "Backup before pull $(date +%Y%m%d_%H%M%S)"
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
        if git stash pop; then
            echo "   ✅ Stash'dan qaytarildi"
        else
            echo "   ⚠️  Stash conflict bor, qo'lda hal qiling"
            echo "   Backup: $BACKUP_DIR"
        fi
    fi
else
    echo "   ❌ Pull xatolik!"
    echo "   Backup: $BACKUP_DIR"
    exit 1
fi

# 6. Service restart (agar kerak bo'lsa)
echo ""
echo "6. Service restart qilinmoqda..."
sudo systemctl restart hrbot
sleep 2
sudo systemctl status hrbot --no-pager -l | head -5

echo ""
echo "✅ Tugadi!"
```

## 3. Tezkor Buyruqlar

### Xavfsiz pull (bitta buyruq)

```bash
cd /root/geeks_hr_bot && \
git add wsgi.py 2>/dev/null && \
git commit -m "Add wsgi.py" 2>/dev/null || true && \
git stash 2>/dev/null || true && \
git pull && \
git stash pop 2>/dev/null || true && \
sudo systemctl restart hrbot
```

### Force pull (ehtiyot bo'ling)

```bash
cd /root/geeks_hr_bot
git fetch origin
git reset --hard origin/main  # yoki master
sudo systemctl restart hrbot
```

## 4. Muammolarni Oldini Olish

### .gitignore faylini sozlash

```bash
# .gitignore faylida quyidagilarni qo'shing:
nano .gitignore
```

Quyidagilarni qo'shing:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
env/

# Environment
.env
.env.local

# Database
*.db
*.sqlite
*.sqlite3

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Backup
*.backup
*.bak
*_backup_*
```

### Pre-pull hook yaratish

```bash
# .git/hooks/pre-pull yaratish
cat > /root/geeks_hr_bot/.git/hooks/pre-pull << 'EOF'
#!/bin/bash
# Pre-pull hook - backup yaratish

BACKUP_DIR="/root/geeks_hr_bot_backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Muhim fayllarni backup qilish
cp app.py "$BACKUP_DIR/" 2>/dev/null
cp config.py "$BACKUP_DIR/" 2>/dev/null
cp wsgi.py "$BACKUP_DIR/" 2>/dev/null
cp .env "$BACKUP_DIR/" 2>/dev/null

echo "Backup yaratildi: $BACKUP_DIR"
EOF

chmod +x /root/geeks_hr_bot/.git/hooks/pre-pull
```

## 5. Avtomatik Deployment Skripti

```bash
#!/bin/bash
# auto-deploy.sh

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
source .venv/bin/activate
pip install -r requirements.txt --quiet

# 3. Database
echo ""
echo "3. Database tekshirish..."
python init_db.py 2>/dev/null || true

# 4. Permissions
echo ""
echo "4. Permissions tuzatish..."
chown -R www-data:www-data . 2>/dev/null || true
chmod 755 . 2>/dev/null || true

# 5. Service restart
echo ""
echo "5. Service restart..."
sudo systemctl restart hrbot
sleep 3

# 6. Status tekshirish
echo ""
echo "6. Status tekshirish..."
if sudo systemctl is-active --quiet hrbot; then
    echo "   ✅ Service ishlayapti"
else
    echo "   ❌ Service ishlamayapti!"
    sudo systemctl status hrbot --no-pager -l | head -10
    exit 1
fi

echo ""
echo "✅ Deployment tugadi!"
```

## 6. Qo'llash

```bash
# Skriptni executable qilish
chmod +x safe-git-pull.sh
chmod +x auto-deploy.sh

# Ishlatish
./safe-git-pull.sh
# yoki
./auto-deploy.sh
```
