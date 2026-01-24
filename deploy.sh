#!/bin/bash
# Deployment script for Geeks HR Bot

set -e  # Exit on error

PROJECT_DIR="/root/geeks_hr_bot"
SERVICE_NAME="hrbot"
DOMAIN="hrbot.geeksandijan.uz"

echo "🚀 Starting deployment..."

# Navigate to project directory
cd $PROJECT_DIR

# Activate virtual environment
source .venv/bin/activate

# Pull latest code (if using git)
# git pull origin main

# Install/update dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Initialize database
echo "💾 Initializing database..."
python init_db.py

# Set permissions
echo "🔐 Setting permissions..."
chown -R www-data:www-data $PROJECT_DIR
chmod +x $PROJECT_DIR/deploy.sh

# Restart service
echo "🔄 Restarting service..."
systemctl restart $SERVICE_NAME

# Check status
echo "✅ Checking service status..."
systemctl status $SERVICE_NAME --no-pager

# Reload nginx
echo "🔄 Reloading nginx..."
nginx -t && systemctl reload nginx

echo "✅ Deployment completed successfully!"