"""
Unit tests for Dynamic Config Manager
"""

import pytest
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from configs.config_manager import (
        DynamicConfigLoader,
        ConfigInjector,
        UnifiedConfigManager,
        ServiceConfig,
        create_sample_config_file
    )
    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False


class TestServiceConfig:
    """Test ServiceConfig dataclass"""
    
    def test_service_config_initialization(self):
        """Test ServiceConfig initialization"""
        config = ServiceConfig("test_service")
        
        assert config.service_name == "test_service"
        assert config.config_data == {}
        assert config.env_prefix == "TEST_SERVICE_"
    
    def test_service_config_with_custom_prefix(self):
        """Test ServiceConfig with custom env prefix"""
        config = ServiceConfig(
            service_name="user_service",
            config_data={"db_url": "postgres://localhost"},
            env_prefix="USER_"
        )
        
        assert config.service_name == "user_service"
        assert config.config_data["db_url"] == "postgres://localhost"
        assert config.env_prefix == "USER_"


@pytest.mark.skipif(not CONFIG_MANAGER_AVAILABLE, reason="Config manager dependencies not available")
class TestDynamicConfigLoader:
    """Test DynamicConfigLoader class"""
    
    def setup_method(self):
        """Setup test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_config.yaml"
    
    def teardown_method(self):
        """Cleanup after test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def create_test_config(self):
        """Create a test configuration file"""
        test_config = {
            "gateway": {
                "host": "127.0.0.1",
                "port": 9000,
                "debug": False,
                "title": "Test Gateway"
            },
            "services": {
                "user_service": {
                    "database_url": "postgresql://test/users",
                    "redis_url": "redis://test:6379/1",
                    "log_level": "DEBUG"
                },
                "product_service": {
                    "database_url": "postgresql://test/products",
                    "cache_ttl": 600
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(test_config, f)
        
        return test_config
    
    def test_initialization_with_existing_file(self):
        """Test loader initialization with existing config file"""
        self.create_test_config()
        
        loader = DynamicConfigLoader(str(self.config_file))
        
        assert loader.config_file == str(self.config_file)
        assert "gateway" in loader.config_data
        assert "services" in loader.config_data
    
    def test_initialization_with_missing_file(self):
        """Test loader initialization with missing config file"""
        non_existent_file = Path(self.temp_dir) / "missing.yaml"
        
        loader = DynamicConfigLoader(str(non_existent_file))
        
        # Should load default config
        assert "gateway" in loader.config_data
        assert loader.config_data["gateway"]["host"] == "0.0.0.0"
        assert loader.config_data["gateway"]["port"] == 8000
    
    def test_get_gateway_config(self):
        """Test getting gateway configuration"""
        self.create_test_config()
        loader = DynamicConfigLoader(str(self.config_file))
        
        gateway_config = loader.get_gateway_config()
        
        assert gateway_config["host"] == "127.0.0.1"
        assert gateway_config["port"] == 9000
        assert gateway_config["debug"] == False
        assert gateway_config["title"] == "Test Gateway"
    
    def test_get_gateway_config_with_env_override(self):
        """Test gateway config with environment variable override"""
        self.create_test_config()
        loader = DynamicConfigLoader(str(self.config_file))
        
        with patch.dict(os.environ, {
            "GATEWAY_HOST": "0.0.0.0",
            "GATEWAY_PORT": "8080",
            "GATEWAY_DEBUG": "true"
        }):
            gateway_config = loader.get_gateway_config()
            
            assert gateway_config["host"] == "0.0.0.0"
            assert gateway_config["port"] == 8080
            assert gateway_config["debug"] == True
    
    def test_get_service_config(self):
        """Test getting service configuration"""
        self.create_test_config()
        loader = DynamicConfigLoader(str(self.config_file))
        
        user_config = loader.get_service_config("user_service")
        
        assert user_config["database_url"] == "postgresql://test/users"
        assert user_config["redis_url"] == "redis://test:6379/1"
        assert user_config["log_level"] == "DEBUG"
    
    def test_get_service_config_with_env_override(self):
        """Test service config with environment variable override"""
        self.create_test_config()
        loader = DynamicConfigLoader(str(self.config_file))
        
        with patch.dict(os.environ, {
            "USER_SERVICE_DATABASE_URL": "postgresql://override/users",
            "USER_SERVICE_LOG_LEVEL": "INFO"
        }):
            user_config = loader.get_service_config("user_service")
            
            assert user_config["database_url"] == "postgresql://override/users"
            assert user_config["log_level"] == "INFO"
            assert user_config["redis_url"] == "redis://test:6379/1"  # Not overridden
    
    def test_convert_env_value(self):
        """Test environment value conversion"""
        loader = DynamicConfigLoader(str(self.config_file))
        
        # Test boolean conversion
        assert loader._convert_env_value("true", False) == True
        assert loader._convert_env_value("false", True) == False
        assert loader._convert_env_value("1", False) == True
        assert loader._convert_env_value("0", True) == False
        
        # Test integer conversion
        assert loader._convert_env_value("123", 0) == 123
        assert loader._convert_env_value("invalid", 0) == 0  # Fallback
        
        # Test float conversion
        assert loader._convert_env_value("12.34", 0.0) == 12.34
        assert loader._convert_env_value("invalid", 0.0) == 0.0  # Fallback
        
        # Test string (no conversion)
        assert loader._convert_env_value("test", "original") == "test"
    
    def test_get_all_service_configs(self):
        """Test getting all service configurations"""
        self.create_test_config()
        loader = DynamicConfigLoader(str(self.config_file))
        
        all_configs = loader.get_all_service_configs()
        
        assert "user_service" in all_configs
        assert "product_service" in all_configs
        assert all_configs["user_service"]["database_url"] == "postgresql://test/users"
        assert all_configs["product_service"]["cache_ttl"] == 600
    
    def test_reload_config(self):
        """Test configuration reloading"""
        self.create_test_config()
        loader = DynamicConfigLoader(str(self.config_file))
        
        # Modify config file
        modified_config = {
            "gateway": {"host": "new-host", "port": 7000},
            "services": {"new_service": {"setting": "value"}}
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(modified_config, f)
        
        loader.reload_config()
        
        assert loader.config_data["gateway"]["host"] == "new-host"
        assert loader.config_data["gateway"]["port"] == 7000
        assert "new_service" in loader.config_data["services"]


@pytest.mark.skipif(not CONFIG_MANAGER_AVAILABLE, reason="Config manager dependencies not available")
class TestConfigInjector:
    """Test ConfigInjector class"""
    
    def setup_method(self):
        """Setup test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_config.yaml"
        
        # Create test config
        test_config = {
            "gateway": {"host": "127.0.0.1", "port": 8000},
            "services": {
                "test_service": {
                    "database_url": "postgresql://test/db",
                    "api_key": "test-key",
                    "timeout": 30,
                    "debug": True
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(test_config, f)
        
        self.loader = DynamicConfigLoader(str(self.config_file))
        self.injector = ConfigInjector(self.loader)
    
    def teardown_method(self):
        """Cleanup after test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_inject_service_config(self):
        """Test injecting service configuration into environment"""
        test_env = {}
        
        config = self.injector.inject_service_config("test_service", test_env)
        
        # Check returned config
        assert config["database_url"] == "postgresql://test/db"
        assert config["api_key"] == "test-key"
        assert config["timeout"] == 30
        assert config["debug"] == True
        
        # Check environment injection
        assert test_env["TEST_SERVICE_DATABASE_URL"] == "postgresql://test/db"
        assert test_env["TEST_SERVICE_API_KEY"] == "test-key"
        assert test_env["TEST_SERVICE_TIMEOUT"] == "30"
        assert test_env["TEST_SERVICE_DEBUG"] == "True"
    
    def test_inject_all_configs(self):
        """Test injecting all service configurations"""
        test_env = {}
        
        all_configs = self.injector.inject_all_configs(test_env)
        
        assert "test_service" in all_configs
        assert "TEST_SERVICE_DATABASE_URL" in test_env
    
    def test_get_injected_config(self):
        """Test getting previously injected configuration"""
        # First inject
        self.injector.inject_service_config("test_service")
        
        # Then get
        config = self.injector.get_injected_config("test_service")
        
        assert config is not None
        assert config["database_url"] == "postgresql://test/db"
    
    def test_get_injected_config_non_existent(self):
        """Test getting non-existent injected configuration"""
        config = self.injector.get_injected_config("non_existent")
        assert config is None


@pytest.mark.skipif(not CONFIG_MANAGER_AVAILABLE, reason="Config manager dependencies not available")
class TestUnifiedConfigManager:
    """Test UnifiedConfigManager class"""
    
    def setup_method(self):
        """Setup test method"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_config.yaml"
        
        # Create comprehensive test config
        test_config = {
            "gateway": {
                "host": "127.0.0.1",
                "port": 8000,
                "debug": True,
                "title": "Test Gateway"
            },
            "services": {
                "user_service": {
                    "database_url": "postgresql://test/users",
                    "redis_url": "redis://test:6379/1"
                },
                "product_service": {
                    "database_url": "postgresql://test/products",
                    "cache_ttl": 300
                }
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(test_config, f)
        
        self.manager = UnifiedConfigManager(str(self.config_file))
    
    def teardown_method(self):
        """Cleanup after test"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test manager initialization"""
        assert self.manager.config_loader is not None
        assert self.manager.config_injector is not None
        assert isinstance(self.manager.service_settings, dict)
    
    def test_setup_service_config(self):
        """Test setting up service configuration"""
        config = self.manager.setup_service_config("user_service")
        
        assert config["database_url"] == "postgresql://test/users"
        assert config["redis_url"] == "redis://test:6379/1"
        assert "user_service" in self.manager.service_settings
    
    def test_setup_all_services(self):
        """Test setting up all service configurations"""
        all_configs = self.manager.setup_all_services()
        
        assert "user_service" in all_configs
        assert "product_service" in all_configs
        assert len(self.manager.service_settings) == 2
    
    def test_get_gateway_config(self):
        """Test getting gateway configuration"""
        config = self.manager.get_gateway_config()
        
        assert config["host"] == "127.0.0.1"
        assert config["port"] == 8000
        assert config["debug"] == True
        assert config["title"] == "Test Gateway"
    
    def test_get_config_status(self):
        """Test getting configuration status"""
        # Setup some services first
        self.manager.setup_service_config("user_service")
        
        status = self.manager.get_config_status()
        
        assert "gateway_config" in status
        assert "loaded_services" in status
        assert "injected_configs" in status
        assert "config_file" in status
        assert "total_services" in status
        
        assert len(status["loaded_services"]) == 1
        assert "user_service" in status["loaded_services"]
    
    def test_validate_service_config(self):
        """Test service configuration validation"""
        # Setup service first
        self.manager.setup_service_config("user_service")
        
        validation = self.manager.validate_service_config("user_service")
        
        assert validation["valid"] == True
        assert validation["service_name"] == "user_service"
        assert "config" in validation
    
    def test_validate_non_existent_service_config(self):
        """Test validating non-existent service configuration"""
        validation = self.manager.validate_service_config("non_existent")
        
        assert validation["valid"] == False
        assert "error" in validation


def test_create_sample_config_file():
    """Test creating sample configuration file"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_file = Path(temp_dir) / "sample_config.yaml"
        
        create_sample_config_file(str(config_file))
        
        assert config_file.exists()
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        assert "gateway" in config
        assert "services" in config
        assert "user_service" in config["services"]
        assert "product_service" in config["services"]


# Fixtures
@pytest.fixture
def sample_config_data():
    """Fixture providing sample configuration data"""
    return {
        "gateway": {
            "host": "0.0.0.0",
            "port": 8000,
            "debug": True
        },
        "services": {
            "test_service": {
                "database_url": "postgresql://localhost/test",
                "api_key": "test-key",
                "timeout": 30
            }
        }
    }


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
