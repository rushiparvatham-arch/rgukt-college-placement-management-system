import os
from flask import Flask, jsonify, request
from flask_cors import CORS

from app.config import Config
from app.extensions import db, oauth, AUTHLIB_AVAILABLE


def create_app():
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
    )
    app.config.from_object(Config)
    # PROPAGATE_EXCEPTIONS=False ensures our JSON error handlers below actually
    # run for /api/* routes even with debug=True — otherwise Flask lets the
    # interactive HTML debugger intercept exceptions first, and the frontend's
    # fetch() can't parse that as JSON. Full tracebacks are still logged to the
    # terminal via app.logger.exception() for local debugging.
    app.config["PROPAGATE_EXCEPTIONS"] = False

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["PROFILE_PICTURE_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "instance"), exist_ok=True)

    db.init_app(app)
    CORS(app, supports_credentials=True)

    # Google OAuth client — only registered when Authlib is installed AND
    # credentials are configured. app.config["GOOGLE_OAUTH_ENABLED"] lets
    # routes/frontend check this cleanly instead of pretending Google
    # Sign-In works when it hasn't been set up (or crashing if the optional
    # `Authlib` dependency was never installed — see app/extensions.py).
    app.config["GOOGLE_OAUTH_ENABLED"] = bool(
        AUTHLIB_AVAILABLE
        and app.config.get("GOOGLE_CLIENT_ID")
        and app.config.get("GOOGLE_CLIENT_SECRET")
    )
    if app.config["GOOGLE_OAUTH_ENABLED"]:
        oauth.init_app(app)
        oauth.register(
            name="google",
            client_id=app.config["GOOGLE_CLIENT_ID"],
            client_secret=app.config["GOOGLE_CLIENT_SECRET"],
            server_metadata_url=app.config["GOOGLE_DISCOVERY_URL"],
            client_kwargs={"scope": "openid email profile"},
        )
    elif app.config.get("GOOGLE_CLIENT_ID") and not AUTHLIB_AVAILABLE:
        app.logger.warning(
            "GOOGLE_CLIENT_ID is set but the 'Authlib' package isn't installed — "
            "Google Sign-In will show as 'not configured'. Run: pip install -r requirements.txt"
        )

    from app.routes.pages import pages_bp
    from app.routes.auth import auth_bp
    from app.routes.student import student_bp
    from app.routes.cdpc import cdpc_bp
    from app.routes.company import company_bp
    from app.routes.common import common_bp

    app.register_blueprint(pages_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(student_bp, url_prefix="/api/student")
    app.register_blueprint(cdpc_bp, url_prefix="/api/cdpc")
    app.register_blueprint(company_bp, url_prefix="/api/company")
    app.register_blueprint(common_bp, url_prefix="/api/common")

    # Global error handlers: any unhandled exception on an /api/* route returns
    # clean JSON instead of an HTML traceback page (which the frontend's fetch()
    # can't parse as JSON — and never expose raw Python errors to the client).
    @app.errorhandler(404)
    def handle_404(e):
        if request.path.startswith("/api/"):
            return jsonify({"error": "The requested resource was not found."}), 404
        return e

    @app.errorhandler(500)
    def handle_500(e):
        app.logger.exception("Unhandled server error")
        db.session.rollback()
        if request.path.startswith("/api/"):
            return jsonify({"error": "Something went wrong on our end. Please try again."}), 500
        return e

    @app.errorhandler(Exception)
    def handle_uncaught(e):
        from werkzeug.exceptions import HTTPException
        if isinstance(e, HTTPException):
            return e
        app.logger.exception("Unhandled exception")
        db.session.rollback()
        if request.path.startswith("/api/"):
            return jsonify({"error": "Something went wrong on our end. Please try again."}), 500
        raise e

    with app.app_context():
        db.create_all()
        from app.seed import seed_data
        seed_data()

    return app

