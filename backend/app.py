"""
Akkerman Backend API

A stateless Flask application with SQLAlchemy database integration.
This service provides HTTP endpoints and manages database connections efficiently.

Key Features:
- Configurable database connection (SQLite default, override with DATABASE_URL)
- Connection pooling with verification and recycling
- Health check endpoint (/healthz)
- Extensible architecture for adding routes and models
"""

from flask import Flask, jsonify
import logging
import sys

from config import get_config
from database import init_db, check_database_health


def create_app(config=None):
    """
    Application factory function
    
    Args:
        config: Configuration class or instance (uses FLASK_ENV if not provided)
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    if config is None:
        config = get_config()
    app.config.from_object(config)
    
    # Initialize logging
    setup_logging(app)
    
    # Initialize database
    init_db(app)
    
    # Register routes
    register_routes(app)
    
    # Log startup info
    app.logger.info(f"Application started with config: {config.__name__}")
    app.logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
    
    return app


def register_routes(app):
    """Register all application routes"""
    
    @app.route('/healthz', methods=['GET'])
    def healthz():
        """
        Health check endpoint
        
        Returns 200 OK if the application and database are healthy.
        Returns 503 Service Unavailable if the database is unreachable.
        
        Response:
            {
                "status": "healthy" | "unhealthy",
                "database": "connected" | "error message"
            }
        """
        is_healthy, error = check_database_health(app)
        
        if is_healthy:
            return jsonify({
                "status": "healthy",
                "database": "connected"
            }), 200
        else:
            return jsonify({
                "status": "unhealthy",
                "database": error
            }), 503
    
    @app.route('/api/v1/status', methods=['GET'])
    def status():
        """
        Application status endpoint
        Returns version and basic information
        """
        return jsonify({
            "version": get_app_version(),
            "status": "running",
            "service": "akkerman-backend"
        }), 200


def setup_logging(app):
    """Configure application logging"""
    
    # Remove default Flask logger handler
    app.logger.handlers.clear()
    
    # Create console handler with formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


def get_app_version():
    """Read version from VERSION.txt in root directory"""
    try:
        with open('../VERSION.txt', 'r') as f:
            return f.read().strip()
    except:
        return "0.1.0"


if __name__ == '__main__':
    app = create_app()
    # Run with development server (not recommended for production)
    # In production, use: gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
    app.run(host='0.0.0.0', port=5000, debug=False)
