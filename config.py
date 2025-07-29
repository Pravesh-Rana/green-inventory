# config.py

import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    # Core Flask and Database Config
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Store Manager's email (recipient of alerts)
    STORE_MANAGER_EMAIL = os.environ.get('STORE_MANAGER_EMAIL')

    # API Keys for AI and Search
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    SERPER_API_KEY = os.environ.get('SERPER_API_KEY')
    
    # Email Configuration using SendGrid
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    SENDER_EMAIL = os.environ.get('SENDER_EMAIL')