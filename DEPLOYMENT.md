# Deployment Guide for cPanel (ahost.uz)

## Step 1: Upload Files to cPanel

1. Log in to your cPanel account
2. Navigate to **File Manager**
3. Upload all project files to your domain's root directory (usually `public_html` or a subdomain folder):
   - `app.py`
   - `config.py`
   - `passenger_wsgi.py`
   - `requirements.txt`
   - `init_db.py` (if needed)
   - `hr_bot.db` (will be created automatically if it doesn't exist)

## Step 2: Install Python Dependencies

1. In cPanel, go to **Python App** or **Setup Python App**
2. Create a new Python application:
   - **Python version**: Choose Python 3.7 or higher
   - **App root**: Select your project directory
   - **App URL**: Choose your domain/subdomain
   - **Startup file**: `passenger_wsgi.py`
3. Click **Create**
4. In the application details, find **Pip Install** section
5. Click **Install from requirements.txt** or manually install:
   ```
   pip install telepot==12.7 flask==3.0.0 openpyxl==3.1.2
   ```

## Step 3: Set Up Webhook

After your application is running, you need to set the Telegram webhook:

1. Replace `YOUR_DOMAIN` with your actual domain (e.g., `https://yourdomain.ahost.uz` or `https://subdomain.yourdomain.ahost.uz`)
2. Replace `YOUR_BOT_TOKEN` with your actual bot token from `config.py`

**Option A: Using the webhook setup endpoint**
Visit in your browser:
```
https://YOUR_DOMAIN/setwebhook?url=https://YOUR_DOMAIN/YOUR_BOT_TOKEN
```

**Option B: Using Telegram API directly**
Visit in your browser (replace with your actual values):
```
https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook?url=https://YOUR_DOMAIN/YOUR_BOT_TOKEN
```

**Example:**
If your domain is `https://bot.example.ahost.uz` and your token is `8423618425:AAGslrdY8jGmiHdEt65dyoUkWWwU8roORjE`, the URL would be:
```
https://bot.example.ahost.uz/setwebhook?url=https://bot.example.ahost.uz/8423618425:AAGslrdY8jGmiHdEt65dyoUkWWwU8roORjE
```

## Step 4: Verify Webhook is Set

Visit in your browser:
```
https://api.telegram.org/botYOUR_BOT_TOKEN/getWebhookInfo
```

You should see your webhook URL in the response.

## Step 5: Test the Bot

1. Send `/start` to your bot in Telegram
2. Check if the bot responds
3. Visit `https://YOUR_DOMAIN/` to see if the Flask app is running (should show "Geeks Andijan HR Bot ishlamoqda...")

## Troubleshooting

### Bot not responding?
1. Check if the webhook is set correctly using `getWebhookInfo`
2. Check cPanel error logs: **Errors** section in cPanel
3. Check Python application logs in cPanel Python App section
4. Make sure all dependencies are installed correctly

### Webhook not working?
1. Make sure your domain has SSL certificate (HTTPS is required for webhooks)
2. Check if the webhook URL is accessible (should return "ok" when accessed)
3. Verify the token in the webhook URL matches your bot token

### Database issues?
1. Make sure the `hr_bot.db` file has write permissions
2. The database will be created automatically if it doesn't exist
3. Check file permissions in cPanel File Manager

## Important Notes

- **HTTPS is required**: Telegram webhooks require HTTPS. Make sure your domain has an SSL certificate.
- **File permissions**: Ensure the database file and project directory have proper read/write permissions.
- **Python version**: Use Python 3.7 or higher.
- **Restart app**: After making changes, restart your Python application in cPanel.

## Removing Webhook (for testing)

If you need to switch back to polling mode for testing:
```
https://YOUR_DOMAIN/deletewebhook
```

Or use Telegram API:
```
https://api.telegram.org/botYOUR_BOT_TOKEN/deleteWebhook
```

