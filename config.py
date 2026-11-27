
import os

# Deteksi apakah berjalan di Vercel (serverless) atau lokal
IS_VERCEL = os.environ.get('VERCEL', '') == '1'

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'sentimen-ai-ekonomi-digital-2026')
    # Vercel hanya bisa menulis ke /tmp — SQLite harus di sana
    if IS_VERCEL:
        SQLALCHEMY_DATABASE_URI = 'sqlite:////tmp/sentimen_ai.db'
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///social_monitor.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
