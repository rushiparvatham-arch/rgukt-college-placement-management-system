from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Authlib (Google OAuth) is an optional dependency — the whole app must still
# start and run normally without it, with Google Sign-In simply disabled,
# rather than crashing on import. See app/__init__.py for how this flag is used.
try:
    from authlib.integrations.flask_client import OAuth
    oauth = OAuth()
    AUTHLIB_AVAILABLE = True
except ImportError:
    oauth = None
    AUTHLIB_AVAILABLE = False
