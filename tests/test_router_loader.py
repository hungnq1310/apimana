"""
Unit tests for Dynamic Router Loader
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from configs.router_loader import (
        DynamicRouterLoader, 
        RouterConfig, 
        create_test_router
    )
    from fastapi import FastAPI, APIRouter
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestRouterConfig:
    """Test RouterConfig class"""
    
    def test_router_config_defaults(self):
        """Test RouterConfig default values"""
        config = RouterConfig(
            service_name="test_service",
            module_path="/path/to/module.py"
        )
        
        assert config.service_name == "test_service"
        assert config.module_path == "/path/to/module.py"
        assert config.router_name == "router"
        assert config.prefix == "/test_service"
        assert config.tags == ["Test Service"]
        assert config.include_endpoints is None
        assert config.exclude_endpoints is None
        assert config.config_name == "test_service"
    
    def test_router_config_custom_values(self):
        """Test RouterConfig with custom values"""
        config = RouterConfig(
            service_name="user_service",
            module_path="/path/to/user.py",
            router_name="user_router",
            prefix="/api/v1/users",
            tags=["Users", "Authentication"],
            include_endpoints={"/login", "/register"},
            exclude_endpoints={"/admin"},
            config_name="users"
        )
        
        assert config.service_name == "user_service"
        assert config.prefix == "/api/v1/users"
        assert config.tags == ["Users", "Authentication"]
        assert config.include_endpoints == {"/login", "/register"}
        assert config.exclude_endpoints == {"/admin"}
        assert config.config_name == "users"


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
class TestDynamicRouterLoader:
    """Test DynamicRouterLoader class"""
    
    def setup_method(self):
        """Setup test method"""
        self.loader = DynamicRouterLoader()
    
    def test_initialization(self):
        """Test loader initialization"""
        assert isinstance(self.loader.loaded_routers, dict)
        assert isinstance(self.loader.failed_loads, dict)
        assert isinstance(self.loader.router_configs, list)
        assert len(self.loader.loaded_routers) == 0
        assert len(self.loader.failed_loads) == 0
    
    def test_add_external_path(self):
        """Test adding external path to sys.path"""
        test_path = "/test/path"
        original_path = sys.path.copy()
        
        self.loader.add_external_path(test_path)
        
        assert test_path in sys.path
        
        # Cleanup
        sys.path = original_path
    
    def test_get_status(self):
        """Test get_status method"""
        status = self.loader.get_status()
        
        assert "loaded_routers" in status
        assert "failed_loads" in status
        assert "total_loaded" in status
        assert "total_failed" in status
        assert status["total_loaded"] == 0
        assert status["total_failed"] == 0
    
    def test_get_router(self):
        """Test getting router by service name"""
        # Test non-existent router
        router = self.loader.get_router("non_existent")
        assert router is None
        
        # Add a mock router
        mock_router = Mock(spec=APIRouter)
        self.loader.loaded_routers["test_service"] = mock_router
        
        router = self.loader.get_router("test_service")
        assert router is mock_router
    
    @patch('importlib.util.spec_from_file_location')
    @patch('importlib.util.module_from_spec')
    def test_load_router_from_path_success(self, mock_module_from_spec, mock_spec_from_file):
        """Test successful router loading from path"""
        # Setup mocks
        mock_spec = Mock()
        mock_spec.loader = Mock()
        mock_spec_from_file.return_value = mock_spec
        
        mock_module = Mock()
        mock_router = Mock(spec=APIRouter)
        mock_module.router = mock_router
        mock_module_from_spec.return_value = mock_module
        
        # Test config
        config = RouterConfig(
            service_name="test_service",
            module_path="/path/to/test.py"
        )
        
        # Load router
        result = self.loader.load_router_from_path(config)
        
        # Assertions
        assert result is mock_router
        assert "test_service" in self.loader.loaded_routers
        assert self.loader.loaded_routers["test_service"] is mock_router
    
    @patch('importlib.util.spec_from_file_location')
    def test_load_router_from_path_failure(self, mock_spec_from_file):
        """Test router loading failure"""
        # Setup mock to raise exception
        mock_spec_from_file.side_effect = ImportError("Module not found")
        
        config = RouterConfig(
            service_name="test_service", 
            module_path="/path/to/test.py"
        )
        
        result = self.loader.load_router_from_path(config)
        
        assert result is None
        assert "test_service" in self.loader.failed_loads
        assert "Module not found" in self.loader.failed_loads["test_service"]
    
    def test_filter_router_endpoints(self):
        """Test endpoint filtering"""
        # Create mock router with routes
        original_router = Mock(spec=APIRouter)
        
        # Create mock routes
        route1 = Mock()
        route1.path = "/users"
        route1.name = "get_users"
        
        route2 = Mock()
        route2.path = "/users/{id}"
        route2.name = "get_user"
        
        route3 = Mock()
        route3.path = "/admin"
        route3.name = "admin_panel"
        
        original_router.routes = [route1, route2, route3]
        
        # Test config with include endpoints
        config = RouterConfig(
            service_name="test_service",
            module_path="/path/to/test.py",
            include_endpoints={"/users"},
            prefix="/api/test",
            tags=["Test"]
        )
        
        with patch('fastapi.APIRouter') as mock_router_class:
            mock_new_router = Mock(spec=APIRouter)
            mock_new_router.routes = []
            mock_router_class.return_value = mock_new_router
            
            result = self.loader._filter_router_endpoints(original_router, config)
            
            # Should create new router with filtered routes
            mock_router_class.assert_called_once_with(
                prefix="/api/test",
                tags=["Test"]
            )


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
def test_create_test_router():
    """Test test router creation"""
    router = create_test_router()
    
    assert isinstance(router, APIRouter)
    assert len(router.routes) >= 2  # Should have at least test and health endpoints


class TestRouterLoaderWithoutFastAPI:
    """Test router loader functionality that doesn't require FastAPI"""
    
    def test_router_config_without_fastapi(self):
        """Test RouterConfig creation without FastAPI"""
        config = RouterConfig(
            service_name="test_service",
            module_path="/path/to/module.py"
        )
        
        assert config.service_name == "test_service"
        assert config.module_path == "/path/to/module.py"


# Fixture for creating test configs
@pytest.fixture
def sample_router_configs():
    """Fixture providing sample router configurations"""
    return [
        RouterConfig(
            service_name="user_service",
            module_path="/path/to/user.py",
            prefix="/api/v1/users",
            tags=["Users"],
            include_endpoints={"/users", "/auth"}
        ),
        RouterConfig(
            service_name="product_service",
            module_path="/path/to/product.py", 
            prefix="/api/v1/products",
            tags=["Products"],
            exclude_endpoints={"/admin"}
        )
    ]


@pytest.mark.skipif(not FASTAPI_AVAILABLE, reason="FastAPI not available")
def test_load_all_routers_integration(sample_router_configs):
    """Integration test for loading multiple routers"""
    loader = DynamicRouterLoader()
    app = Mock(spec=FastAPI)
    
    with patch.object(loader, 'load_router_from_path') as mock_load:
        # Mock successful loading
        mock_router = Mock(spec=APIRouter)
        mock_load.return_value = mock_router
        
        results = loader.load_all_routers(app, sample_router_configs)
        
        # Should attempt to load all configs
        assert len(results) == len(sample_router_configs)
        assert all(results.values())  # All should succeed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
