"""
Passenger WSGI file for cPanel deployment
This file is required for Python applications on cPanel with Passenger
"""
import os
import sys

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Set webhook mode environment variable BEFORE importing app
# This ensures webhook mode is active and no polling code runs
os.environ['WEBHOOK_MODE'] = 'true'

# Import the Flask app (after setting environment variable)
from app import app, ensure_db

# Initialize database on startup
try:
    ensure_db()
except Exception as e:
    # Log error but don't fail startup
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    logger.error(f"Error initializing database: {e}")

# Passenger expects 'application' variable
application = app

# Note: Do NOT run app.run() here - Passenger handles the server
# The webhook will receive updates via Flask routes

