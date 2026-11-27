
import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'social-monitor-local-2026')
    SQLALCHEMY_DATABASE_URI = 'sqlite:///social_monitor.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024