"""
Database and Application Configuration

This module provides environment-driven configuration for the Flask application.
Database connection is fully configurable via environment variables.

Connection pooling best practices:
- pool_pre_ping: Verifies connection before use (prevents "lost connection" errors)
- pool_recycle: Recycles connections after 3600 seconds to prevent MySQL timeouts
- pool_size: Number of connections to maintain in the pool
- max_overflow: Additional connections that can be created beyond pool_size
"""

import os
from urllib.parse import quote_plus


class Config:
    """Base configuration for the Flask application"""
    
    # Application settings
    DEBUG = False
    TESTING = False
    
    # SQLAlchemy configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Build database URI from environment variables
    # Default: SQLite (file-based, no external dependencies)
    # Override with DATABASE_URL env var for PostgreSQL, MySQL, etc.
    _database_url = os.getenv('DATABASE_URL')
    
    if _database_url:
        SQLALCHEMY_DATABASE_URI = _database_url
    else:
        # SQLite default (ensures no external DB required for local development)
        SQLALCHEMY_DATABASE_URI = os.getenv(
            'SQLALCHEMY_DATABASE_URI',
            'sqlite:///./akkerman.db'
        )
    
    # Connection pooling configuration
    # These settings apply to all database backends (SQLite, PostgreSQL, MySQL, etc.)
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,        # Verify connection before use
        'pool_recycle': 3600,          # Recycle connections after 1 hour
        'pool_size': int(os.getenv('DB_POOL_SIZE', '5')),
        'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', '10')),
        'echo': os.getenv('SQLALCHEMY_ECHO', 'False').lower() == 'true',
    }


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ENGINE_OPTIONS = {
        **Config.SQLALCHEMY_ENGINE_OPTIONS,
        'echo': True,  # Log SQL queries in development
    }


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Use in-memory DB for tests
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': False,
        'poolclass': None,  # Disable pooling for in-memory tests
    }


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # In production, DATABASE_URL should be set in environment
    # Example: postgresql://user:password@host:5432/dbname


def get_config():
    """Get configuration based on FLASK_ENV environment variable"""
    env = os.getenv('FLASK_ENV', 'development')
    
    config_map = {
        'development': DevelopmentConfig,
        'testing': TestingConfig,
        'production': ProductionConfig,
    }
    
    return config_map.get(env, DevelopmentConfig)
