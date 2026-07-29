"""
Unit tests for the Akkerman backend application

Tests verify:
- Health endpoint returns 200 when application is up
- Database connectivity is properly tested
- Application configuration is correct
"""

import pytest
import json
from app import create_app
from config import TestingConfig


@pytest.fixture
def app():
    """Create and configure a test app instance"""
    app = create_app(TestingConfig)
    return app


@pytest.fixture
def client(app):
    """A test client for the app"""
    return app.test_client()


class TestHealthEndpoint:
    """Tests for the /healthz endpoint"""
    
    def test_healthz_returns_200(self, client):
        """Test that /healthz endpoint returns 200 OK"""
        response = client.get('/healthz')
        assert response.status_code == 200
    
    def test_healthz_returns_json(self, client):
        """Test that /healthz returns valid JSON"""
        response = client.get('/healthz')
        assert response.content_type == 'application/json'
        
        data = json.loads(response.data)
        assert 'status' in data
        assert 'database' in data
    
    def test_healthz_reports_healthy(self, client):
        """Test that /healthz reports healthy status when DB is OK"""
        response = client.get('/healthz')
        data = json.loads(response.data)
        
        assert data['status'] == 'healthy'
        assert data['database'] == 'connected'


class TestStatusEndpoint:
    """Tests for the /api/v1/status endpoint"""
    
    def test_status_returns_200(self, client):
        """Test that /api/v1/status endpoint returns 200 OK"""
        response = client.get('/api/v1/status')
        assert response.status_code == 200
    
    def test_status_returns_version(self, client):
        """Test that status endpoint includes version information"""
        response = client.get('/api/v1/status')
        data = json.loads(response.data)
        
        assert 'version' in data
        assert 'status' in data
        assert 'service' in data
        assert data['service'] == 'akkerman-backend'


class TestApplicationConfiguration:
    """Tests for application configuration"""
    
    def test_app_uses_test_config(self, app):
        """Test that test config is applied correctly"""
        assert app.config['TESTING'] is True
    
    def test_test_database_is_in_memory(self, app):
        """Test that test environment uses in-memory SQLite"""
        assert ':memory:' in app.config['SQLALCHEMY_DATABASE_URI']
    
    def test_app_logger_configured(self, app):
        """Test that application logger is properly configured"""
        assert app.logger is not None
        assert len(app.logger.handlers) > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
