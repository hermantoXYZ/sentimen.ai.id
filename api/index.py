"""
Vercel Serverless Entry Point
Flask app di-expose sebagai handler WSGI untuk Vercel Python Runtime.
"""
import sys
import os

# Pastikan root project ada di sys.path agar import app, layanan, model bisa jalan
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

# Vercel Python runtime memanggil variabel `app` sebagai WSGI/ASGI handler
# Bisa juga disebut `handler` — keduanya didukung.
handler = app
