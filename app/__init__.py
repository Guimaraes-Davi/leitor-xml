from flask import Flask


def create_app():
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB

    from app.routes import bp
    app.register_blueprint(bp)

    return app
