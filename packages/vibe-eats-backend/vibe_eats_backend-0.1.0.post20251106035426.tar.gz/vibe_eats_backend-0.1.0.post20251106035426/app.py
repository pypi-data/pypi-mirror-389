from flask import Flask, jsonify
from flask_cors import CORS


def create_app():
    """Application factory function."""

    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes in the app

    # Import and register the blueprint
    from restaurantRoutes import api_blueprint
    from cartRoutes import cart_bp

    app.register_blueprint(api_blueprint, url_prefix="/api")
    app.register_blueprint(cart_bp, url_prefix="/api")

    @app.route("/")
    def home():
        """A simple route to test if the server is running."""
        return jsonify({"message": "Welcome to the Vibe Eats API!"})

    return app
