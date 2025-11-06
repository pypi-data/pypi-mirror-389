"""
Tests unitaires pour ThibEqClient
==================================
"""

import pytest
from thibeq_sdk import (
    ThibEqClient,
    ThibEqError,
    ThibEqAuthError,
    ThibEqValidationError,
    ThibEqNetworkError
)


class TestThibEqClient:
    """Tests du client ThibEquation"""
    
    def test_client_initialization(self):
        """Test l'initialisation du client"""
        client = ThibEqClient(
            base_url="http://localhost:5000",
            api_key="test-key"
        )
        
        assert client.base_url == "http://localhost:5000"
        assert client.api_key == "test-key"
        assert client.timeout == 5.0
        assert client.max_retries == 1
    
    def test_client_custom_config(self):
        """Test l'initialisation avec configuration personnalisée"""
        client = ThibEqClient(
            base_url="http://example.com/",
            api_key="custom-key",
            timeout=10.0,
            max_retries=3
        )
        
        assert client.base_url == "http://example.com"  # trailing slash retiré
        assert client.timeout == 10.0
        assert client.max_retries == 3
    
    def test_headers_format(self):
        """Test le format des headers"""
        client = ThibEqClient(
            base_url="http://localhost:5000",
            api_key="test-key"
        )
        
        assert "X-API-Key" in client._headers
        assert client._headers["X-API-Key"] == "test-key"
        assert client._headers["Content-Type"] == "application/json"
        assert "User-Agent" in client._headers


class TestThibEqExceptions:
    """Tests des exceptions personnalisées"""
    
    def test_base_exception(self):
        """Test l'exception de base"""
        error = ThibEqError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)
    
    def test_auth_exception(self):
        """Test l'exception d'authentification"""
        error = ThibEqAuthError("Auth failed")
        assert isinstance(error, ThibEqError)
    
    def test_validation_exception(self):
        """Test l'exception de validation"""
        error = ThibEqValidationError("Invalid params")
        assert isinstance(error, ThibEqError)
    
    def test_network_exception(self):
        """Test l'exception réseau"""
        error = ThibEqNetworkError("Connection failed")
        assert isinstance(error, ThibEqError)


# Note: Tests d'intégration nécessitant une API en cours d'exécution
# doivent être exécutés séparément (test_smoke.py)
