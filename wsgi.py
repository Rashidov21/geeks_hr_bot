"""
WSGI entry point for Gunicorn
"""
import os
import sys

# Add bot directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Import Flask app
from app import app

# Ensure database is initialized
from app import ensure_db
ensure_db()

# Export application for Gunicorn
application = app

if __name__ == "__main__":
    app.run()
