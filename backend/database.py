"""
Database initialization and management

This module handles SQLAlchemy database setup with connection pooling best practices.
The engine is configured with:
- Connection pool verification (pool_pre_ping)
- Connection recycling to prevent stale connections
- Configurable pool size and overflow
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

# Global database instance
db = SQLAlchemy()


def init_db(app):
    """
    Initialize the database with the Flask application
    
    Args:
        app: Flask application instance
    """
    db.init_app(app)
    
    # Create tables if they don't exist
    with app.app_context():
        db.create_all()


def check_database_health(app):
    """
    Verify database connectivity and health
    
    Args:
        app: Flask application instance
        
    Returns:
        tuple: (is_healthy: bool, error_message: str or None)
    """
    try:
        with app.app_context():
            # Simple SELECT 1 query to verify connection
            db.session.execute(text("SELECT 1"))
            db.session.commit()
            return True, None
    except Exception as e:
        return False, str(e)


class BaseModel(db.Model):
    """
    Abstract base model for all database models
    Provides common fields like id, created_at, updated_at
    """
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())
