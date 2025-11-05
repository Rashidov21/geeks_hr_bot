"""
Passenger WSGI file for cPanel deployment
This file is required for Python applications on cPanel with Passenger
"""
import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set webhook mode environment variable
os.environ['WEBHOOK_MODE'] = 'true'

# Import the Flask app
from app import app, ensure_db

# Initialize database on startup
ensure_db()

# Passenger expects 'application' variable
application = app

if __name__ == "__main__":
    application.run()

