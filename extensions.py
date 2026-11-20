from authlib.integrations.flask_client import OAuth
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect

csrf = CSRFProtect()
oauth = OAuth()
limiter = Limiter(get_remote_address, storage_uri="memory://")