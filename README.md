# Geeks Andijan HR Bot

Telegram bot for managing job applications at Geeks Andijan educational center.

## Features

- 📝 Job application form with step-by-step process
- 👤 Admin panel for viewing and exporting applications
- 📊 Excel export functionality
- 🔒 Secure webhook mode for production
- 💾 SQLite database for data storage
- ✅ Input validation for all fields
- 🔄 Automatic session cleanup to prevent memory leaks
- 🔁 Retry mechanism for message sending

## Requirements

- Python 3.7+
- Telegram Bot Token
- Flask
- SQLite3

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd geeks_hr_bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create `.env` file from `.env.example`:
```bash
cp .env.example .env
```

4. Edit `.env` file and add your configuration:
```env
BOT_TOKEN=your_bot_token_here
ADMIN_ID=your_admin_telegram_id
GROUP_ID=your_group_chat_id
SESSION_TIMEOUT=3600
```

5. Initialize database:
```bash
python init_db.py
```

## Configuration

### Environment Variables

- `BOT_TOKEN`: Your Telegram bot token from BotFather
- `ADMIN_ID`: Your Telegram user ID (admin)
- `GROUP_ID`: Telegram group chat ID for notifications
- `SESSION_TIMEOUT`: Session timeout in seconds (default: 3600)
- `WEBHOOK_MODE`: Set to `true` for production webhook mode
- `WEBHOOK_SECRET`: Optional secret token for webhook security

## Usage

### Local Development (Polling Mode)

```bash
python app.py
```

The bot will run in polling mode, fetching updates from Telegram.

### Production (Webhook Mode)

1. Deploy to your hosting (e.g., cPanel)
2. Set `WEBHOOK_MODE=true` in environment variables
3. Set webhook URL:
```
https://yourdomain.com/setwebhook?url=https://yourdomain.com/YOUR_BOT_TOKEN
```

## Bot Commands

### For Users
- `/start` - Start the application process

### For Admin
- `/start` - Open admin panel
- `/last [vacancy]` - View last 5 applications (optionally filtered by vacancy)
- `/export [vacancy]` - Export all applications to Excel (optionally filtered by vacancy)
- `📋 Oxirgi arizalar` - Button to view last applications
- `📤 Export` - Button to export applications

## Project Structure

```
geeks_hr_bot/
├── app.py              # Main application file
├── config.py           # Configuration module
├── init_db.py          # Database initialization
├── passenger_wsgi.py    # WSGI file for cPanel deployment
├── requirements.txt    # Python dependencies
├── .env.example        # Environment variables template
├── .gitignore         # Git ignore file
└── README.md          # This file
```

## Security Features

- ✅ Environment variables for sensitive data
- ✅ Input validation for all user inputs
- ✅ SQL injection protection (parameterized queries)
- ✅ Webhook secret token support
- ✅ Session timeout and cleanup
- ✅ Proper error handling

## Improvements Made

### Security
- ✅ Moved sensitive data to environment variables
- ✅ Added webhook secret validation
- ✅ Input validation for all fields
- ✅ SQL injection protection

### Performance
- ✅ Database connection context manager
- ✅ User session TTL to prevent memory leaks
- ✅ Retry mechanism for message sending
- ✅ Optimized database queries

### Code Quality
- ✅ Type hints added
- ✅ Comprehensive documentation
- ✅ Removed code duplication
- ✅ Better error handling
- ✅ Proper file handling with context managers

### Features
- ✅ Health check endpoint
- ✅ Better logging
- ✅ Thread-safe user session management
- ✅ Improved validation messages

## Troubleshooting

### Bot not responding
1. Check if webhook is set correctly: `/webhookinfo`
2. Check logs for errors
3. Verify bot token in `.env` file

### Database errors
1. Ensure `hr_bot.db` has write permissions
2. Check database file exists
3. Run `init_db.py` to recreate database

### Webhook issues
1. Ensure HTTPS is enabled (required by Telegram)
2. Verify webhook URL is accessible
3. Check webhook secret if configured

## License

This project is proprietary software for Geeks Andijan.

## Support

For issues and questions, contact the development team.
