import os
import sqlite3
from pathlib import Path
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()

# Pengaman: jika berjalan di Vercel dan tabel auth_user belum ada di /tmp/db.sqlite3,
# otomatis jalankan migrate dan buat akun admin dari Environment Variable.
tmp_db = Path('/tmp/db.sqlite3')
if tmp_db.exists() or not os.access(Path(__file__).resolve().parent.parent, os.W_OK):
    need_migrate = True
    if tmp_db.exists():
        try:
            conn = sqlite3.connect(str(tmp_db))
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='auth_user';")
            if cur.fetchone():
                need_migrate = False
            conn.close()
        except Exception:
            need_migrate = True

    if need_migrate:
        from django.core.management import call_command
        from django.contrib.auth import get_user_model
        call_command('migrate', interactive=False)
        User = get_user_model()
        admin_user = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_pass = os.environ.get('ADMIN_PASSWORD', 'admin12345')
        if not User.objects.filter(username=admin_user).exists():
            User.objects.create_superuser(username=admin_user, email='', password=admin_pass)

app = application