"""Расширения Flask, созданные отдельно от приложения (подключаются в app.create_app)."""
from authlib.integrations.flask_client import OAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()  # защита форм от подделки запросов
oauth = OAuth()       # вход через Google
limiter = Limiter(get_remote_address, storage_uri="memory://")  # лимиты считаются по IP, в памяти
