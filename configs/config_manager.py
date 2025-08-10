"""
Dynamic Configuration Management System for API Gateway

This module provides functionality to dynamically load, manage, and inject
configurations for different services in the API gateway.
"""

import os
import yaml
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, field
from pydantic import Field
from pydantic_settings import BaseSettings as PydanticBaseSettings
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass 
class ServiceConfig:
    """Configuration data for a single service"""
    service_name: str
    config_data: Dict[str, Any] = field(default_factory=dict)
    env_prefix: str = ""
    
    def __post_init__(self):
        """Set default environment prefix if not provided"""
        if not self.env_prefix:
            self.env_prefix = f"{self.service_name.upper()}_"


class DynamicConfigLoader:
    """
    Loads configuration from multiple sources (YAML, environment variables, etc.)
    """
    
    def __init__(self, config_file: str = "gateway_config.yaml"):
        self.config_file = config_file
        self.config_data: Dict[str, Any] = {}
        self.service_configs: Dict[str, ServiceConfig] = {}
        
        # Load environment variables
        load_dotenv()
        
        # Load configuration
        self.load_config()
    
    def load_config(self) -> None:
        """Load configuration from YAML file"""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as file:
                    self.config_data = yaml.safe_load(file) or {}
                logger.info(f"Loaded configuration from {self.config_file}")
            else:
                logger.warning(f"Configuration file {self.config_file} not found, using defaults")
                self.config_data = self._get_default_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self.config_data = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file loading fails"""
        return {
            "gateway": {
                "host": "0.0.0.0",
                "port": 8000,
                "debug": True,
                "title": "Dynamic API Gateway",
                "version": "1.0.0"
            },
            "services": {}
        }
    
    def get_gateway_config(self) -> Dict[str, Any]:
        """Get gateway-specific configuration"""
        gateway_config = self.config_data.get("gateway", {})
        
        # Override with environment variables if available
        gateway_config["host"] = os.getenv("GATEWAY_HOST", gateway_config.get("host", "0.0.0.0"))
        gateway_config["port"] = int(os.getenv("GATEWAY_PORT", str(gateway_config.get("port", 8000))))
        gateway_config["debug"] = os.getenv("GATEWAY_DEBUG", str(gateway_config.get("debug", False))).lower() == "true"
        
        return gateway_config
    
    def get_service_config(self, service_name: str) -> Dict[str, Any]:
        """Get configuration for a specific service"""
        service_config = self.config_data.get("services", {}).get(service_name, {})
        
        # Override with environment variables
        env_prefix = f"{service_name.upper()}_"
        for key, value in service_config.items():
            env_key = f"{env_prefix}{key.upper()}"
            env_value = os.getenv(env_key)
            if env_value is not None:
                # Try to convert to appropriate type
                service_config[key] = self._convert_env_value(env_value, value)
        
        return service_config
    
    def _convert_env_value(self, env_value: str, original_value: Any) -> Any:
        """Convert environment variable string to appropriate type"""
        if isinstance(original_value, bool):
            return env_value.lower() in ('true', '1', 'yes', 'on')
        elif isinstance(original_value, int):
            try:
                return int(env_value)
            except ValueError:
                return original_value
        elif isinstance(original_value, float):
            try:
                return float(env_value)
            except ValueError:
                return original_value
        else:
            return env_value
    
    def get_all_service_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get configurations for all services"""
        services = self.config_data.get("services", {})
        result = {}
        
        for service_name in services.keys():
            result[service_name] = self.get_service_config(service_name)
        
        return result
    
    def reload_config(self) -> None:
        """Reload configuration from file"""
        self.load_config()
        logger.info("Configuration reloaded")


class ConfigInjector:
    """
    Injects configuration into service modules and environments
    """
    
    def __init__(self, config_loader: DynamicConfigLoader):
        self.config_loader = config_loader
        self.injected_configs: Dict[str, Dict[str, Any]] = {}
    
    def inject_service_config(self, service_name: str, target_env: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Inject service configuration into environment or return config dict
        
        Args:
            service_name: Name of the service
            target_env: Target environment dict (defaults to os.environ)
            
        Returns:
            Dict containing the injected configuration
        """
        if target_env is None:
            target_env = os.environ
        
        service_config = self.config_loader.get_service_config(service_name)
        env_prefix = f"{service_name.upper()}_"
        
        # Inject into environment
        for key, value in service_config.items():
            env_key = f"{env_prefix}{key.upper()}"
            target_env[env_key] = str(value)
            logger.debug(f"Injected {env_key}={value}")
        
        # Store for later reference
        self.injected_configs[service_name] = service_config
        
        logger.info(f"Injected configuration for {service_name}")
        return service_config
    
    def inject_all_configs(self, target_env: Optional[Dict[str, str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Inject all service configurations
        
        Args:
            target_env: Target environment dict (defaults to os.environ)
            
        Returns:
            Dict mapping service names to their configurations
        """
        if target_env is None:
            target_env = os.environ
        
        all_configs = self.config_loader.get_all_service_configs()
        result = {}
        
        for service_name in all_configs.keys():
            result[service_name] = self.inject_service_config(service_name, target_env)
        
        return result
    
    def get_injected_config(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get previously injected configuration for a service"""
        return self.injected_configs.get(service_name)



class UnifiedConfigManager:
    """
    Unified configuration manager that combines loading and injection
    """
    
    def __init__(self, config_file: str = "gateway_config.yaml"):
        self.config_loader = DynamicConfigLoader(config_file)
        self.config_injector = ConfigInjector(self.config_loader)
        self.service_settings: Dict[str, Any] = {}
    
    def setup_service_config(self, service_name: str) -> Dict[str, Any]:
        """
        Setup complete configuration for a service
        
        Args:
            service_name: Name of the service to setup
            
        Returns:
            Service configuration dictionary
        """
        # Inject environment variables
        config = self.config_injector.inject_service_config(service_name)
        
        # Create Dict service config
        service_config = self.config_loader.get_service_config(service_name)
        
        # Store settings instance
        self.service_settings[service_name] = service_config
        
        logger.info(f"Setup complete for {service_name}")
        return config
    
    def setup_all_services(self) -> Dict[str, Dict[str, Any]]:
        """Setup configuration for all services"""
        all_configs = {}
        services = self.config_loader.config_data.get("services", {})
        
        for service_name in services.keys():
            all_configs[service_name] = self.setup_service_config(service_name)
        
        return all_configs
    
    def get_gateway_config(self) -> Dict[str, Any]:
        """Get gateway configuration"""
        return self.config_loader.get_gateway_config()
    
    def get_service_settings(self, service_name: str) -> Optional[Any]:
        """Get Pydantic settings instance for a service"""
        return self.service_settings.get(service_name)
    
    def reload_all_configs(self) -> None:
        """Reload all configurations"""
        self.config_loader.reload_config()
        
        # Re-setup all services
        for service_name in self.service_settings.keys():
            self.setup_service_config(service_name)
        
        logger.info("All configurations reloaded")
    
    def get_config_status(self) -> Dict[str, Any]:
        """Get status of configuration management"""
        return {
            "gateway_config": self.get_gateway_config(),
            "loaded_services": list(self.service_settings.keys()),
            "injected_configs": list(self.config_injector.injected_configs.keys()),
            "config_file": self.config_loader.config_file,
            "total_services": len(self.service_settings)
        }
    
    def validate_service_config(self, service_name: str) -> Dict[str, Any]:
        """
        Validate configuration for a service
        
        Args:
            service_name: Name of the service to validate
            
        Returns:
            Validation results
        """
        try:
            settings = self.get_service_settings(service_name)
            if settings is None:
                return {
                    "valid": False,
                    "error": f"No settings found for service {service_name}"
                }
            
            # Try to access all fields to trigger validation
            config_dict = settings.model_dump()
            
            return {
                "valid": True,
                "service_name": service_name,
                "config": config_dict
            }
        
        except Exception as e:
            return {
                "valid": False,
                "service_name": service_name,
                "error": str(e)
            }


# Example usage and testing functions
def create_sample_config_file(filename: str = "gateway_config.yaml") -> None:
    """Create a sample configuration file for testing"""
    sample_config = {
        "gateway": {
            "host": "0.0.0.0",
            "port": 8000,
            "debug": True,
            "title": "Dynamic API Gateway",
            "version": "1.0.0"
        },
        "services": {
            "user_service": {
                "database_url": "postgresql://localhost/gateway_users",
                "redis_url": "redis://localhost:6379/1",
                "jwt_secret": "user-jwt-secret",
                "log_level": "DEBUG"
            },
            "product_service": {
                "database_url": "postgresql://localhost/gateway_products",
                "elasticsearch_url": "http://localhost:9200",
                "cache_ttl": 300,
                "log_level": "INFO"
            }
        }
    }
    
    with open(filename, 'w', encoding='utf-8') as file:
        yaml.dump(sample_config, file, default_flow_style=False)
    
    print(f"Created sample config file: {filename}")


# Testing
if __name__ == "__main__":
    # Create sample config for testing
    create_sample_config_file("test_config.yaml")
    
    # Test the unified config manager
    manager = UnifiedConfigManager("test_config.yaml")
    
    # Setup service configs
    user_config = manager.setup_service_config("user_service")
    print(f"User service config: {user_config}")
    
    # Get gateway config
    gateway_config = manager.get_gateway_config()
    print(f"Gateway config: {gateway_config}")
    
    # Get status
    status = manager.get_config_status()
    print(f"Config status: {status}")
    
    # Validate service config
    validation = manager.validate_service_config("user_service")
    print(f"Validation result: {validation}")
