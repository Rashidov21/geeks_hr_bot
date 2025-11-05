#!/usr/bin/env python3
"""
Quick script to set up webhook for Telegram bot
Run this after deploying to set the webhook URL
"""
import sys
from config import TOKEN

def set_webhook(webhook_url):
    """Set webhook URL for the bot"""
    try:
        import requests
        api_url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
        response = requests.post(api_url, json={"url": webhook_url})
        result = response.json()
        
        if result.get('ok'):
            print(f"✅ Webhook set successfully!")
            print(f"URL: {webhook_url}")
        else:
            print(f"❌ Error setting webhook: {result.get('description', 'Unknown error')}")
            return False
        return True
    except ImportError:
        print("❌ Error: requests library not found. Install it with: pip install requests")
        print("   Or use the web interface: https://YOUR_DOMAIN/setwebhook?url=YOUR_WEBHOOK_URL")
        return False
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False


def get_webhook_info():
    """Get current webhook information"""
    try:
        import requests
        api_url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"
        response = requests.get(api_url)
        result = response.json()
        
        if result.get('ok'):
            info = result.get('result', {})
            print("\n📋 Current Webhook Info:")
            print(f"URL: {info.get('url', 'Not set')}")
            print(f"Pending updates: {info.get('pending_update_count', 0)}")
            print(f"Last error date: {info.get('last_error_date', 'N/A')}")
            print(f"Last error message: {info.get('last_error_message', 'N/A')}")
        else:
            print(f"❌ Error getting webhook info: {result.get('description', 'Unknown error')}")
    except ImportError:
        print("❌ Error: requests library not found. Install it with: pip install requests")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python setup_webhook.py <webhook_url>")
        print("\nExample:")
        print("  python setup_webhook.py https://yourdomain.ahost.uz/8423618425:AAGslrdY8jGmiHdEt65dyoUkWWwU8roORjE")
        print("\nTo check current webhook info:")
        print("  python setup_webhook.py --info")
        sys.exit(1)
    
    if sys.argv[1] == "--info":
        get_webhook_info()
    else:
        webhook_url = sys.argv[1]
        if set_webhook(webhook_url):
            get_webhook_info()

