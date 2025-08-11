"""
Dynamic Router Loading System for API Gateway

This module provides functionality to dynamically load and integrate
routers from external services into the main FastAPI application.
"""

import os
import sys
import importlib
import importlib.util
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
import logging
from fastapi import FastAPI

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RouterConfig:
    """Configuration for a single FastAPI app to be loaded"""
    service_name: str
    module_path: str
    app_name: str = "app"  # Changed from router_name to app_name
    prefix: str = ""
    config_name: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Post-initialization to set default values"""
        if not self.prefix:
            self.prefix = f"/{self.service_name}"
        if not self.config_name:
            self.config_name = self.service_name


class DynamicRouterLoader:
    """
    Dynamically loads and manages routers from external services
    """
    
    def __init__(self):
        self.loaded_apps: Dict[str, FastAPI] = {}  # Only support FastAPI apps
        self.failed_loads: Dict[str, str] = {}
        self.router_configs: List[RouterConfig] = []
    
    def add_external_path(self, path: str) -> None:
        """Add external path to Python sys.path for imports"""
        if path not in sys.path:
            sys.path.insert(0, str(Path(path).resolve()))
            logger.info(f"Added path to sys.path: {path}")
    
    def load_app_from_path(self, config: RouterConfig) -> Optional[FastAPI]:
        """
        Load a FastAPI app from the specified module path
        
        Args:
            config: RouterConfig containing load configuration
            
        Returns:
            FastAPI app instance or None if loading fails
        """
        try:
            # Add external path if needed - handle special case for services with src/ structure
            module_path = Path(config.module_path)
            module_dir = module_path.parent
            
            # For services with src/ structure, add the root directory to path
            # This handles cases like external/docman/src/api/main.py
            if 'src' in module_path.parts:
                # Find the parent directory that contains 'src'
                for i, part in enumerate(module_path.parts):
                    if part == 'src':
                        # Add the directory that contains 'src' to Python path
                        src_parent = Path(*module_path.parts[:i])
                        if src_parent.is_absolute():
                            self.add_external_path(str(src_parent))
                        else:
                            # Make it relative to current working directory
                            self.add_external_path(str(Path.cwd() / src_parent))
                        break
            else:
                # For other services, add the module directory
                self.add_external_path(str(module_dir))
            
            # Import the module
            if Path(config.module_path).suffix == '.py':
                # Load from file path
                spec = importlib.util.spec_from_file_location(
                    f"{config.service_name}_module", 
                    config.module_path
                )
                if spec is None or spec.loader is None:
                    raise ImportError(f"Could not load spec from {config.module_path}")
                    
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
            else:
                # Load from module name
                module = importlib.import_module(config.module_path)
            
            # Get the FastAPI app
            if hasattr(module, config.app_name):
                app_item = getattr(module, config.app_name)
                
                # Check if it's a FastAPI app
                if isinstance(app_item, FastAPI):
                    self.loaded_apps[config.service_name] = app_item
                    logger.info(f"Successfully loaded FastAPI app for {config.service_name}")
                    return app_item
                else:
                    raise TypeError(
                        f"Object '{config.app_name}' in {config.module_path} is not a FastAPI app"
                    )
            else:
                raise AttributeError(
                    f"Module {config.module_path} does not have attribute '{config.app_name}'"
                )
                
        except Exception as e:
            error_msg = f"Failed to load app for {config.service_name}: {str(e)}"
            logger.error(error_msg)
            self.failed_loads[config.service_name] = error_msg
            return None
    
    def load_app(self, app: FastAPI, config: RouterConfig) -> bool:
        """
        Load and mount a single FastAPI app to the main FastAPI app
        
        Args:
            app: FastAPI application instance
            config: RouterConfig for the app to load
            
        Returns:
            bool: True if successful, False otherwise
        """
        service_app = self.load_app_from_path(config)
        if service_app:
            # Use mount to attach the service app
            app.mount(config.prefix, service_app)
            
            self.router_configs.append(config)
            logger.info(
                f"Mounted service {config.service_name} "
                f"at prefix '{config.prefix}'"
            )
            return True
        return False
    
    def load_all_apps(
        self, 
        app: FastAPI, 
        configs: List[RouterConfig]
    ) -> Dict[str, bool]:
        """
        Load and mount multiple routers to the FastAPI app
        
        Args:
            app: FastAPI application instance
            configs: List of RouterConfig objects
            
        Returns:
            Dict mapping service names to success status
        """
        results = {}
        
        for config in configs:
            try:
                success = self.load_app(app, config)
                results[config.service_name] = success
            except Exception as e:
                logger.error(f"Error loading router {config.service_name}: {e}")
                results[config.service_name] = False
        
        # Log summary
        successful = sum(1 for success in results.values() if success)
        total = len(configs)
        logger.info(f"Router loading complete: {successful}/{total} successful")
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get status information about loaded apps"""
        return {
            "loaded_apps": list(self.loaded_apps.keys()),
            "failed_loads": self.failed_loads,
            "total_loaded": len(self.loaded_apps),
            "total_failed": len(self.failed_loads)
        }
    
    def get_app(self, service_name: str) -> Optional[FastAPI]:
        """Get a loaded app by service name"""
        return self.loaded_apps.get(service_name)
    
    def reload_app(self, app: FastAPI, config: RouterConfig) -> bool:
        """
        Reload a specific router (useful for development)
        
        Args:
            app: FastAPI application instance
            config: RouterConfig for the router to reload
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Remove old router if exists
        if config.service_name in self.loaded_apps:
            del self.loaded_apps[config.service_name]
            
        # Clear failed loads for this service
        if config.service_name in self.failed_loads:
            del self.failed_loads[config.service_name]
        
        # Note: For mounting, we would need to recreate the app to properly reload
        # This is a limitation of FastAPI mounting - you can't easily unmount
        logger.warning(
            f"Reloading mounted services requires app restart for {config.service_name}"
        )
        
        # Reload the router
        return self.load_app(app, config)


def create_test_app() -> FastAPI:
    """Create a test FastAPI app for development/testing purposes"""
    test_app = FastAPI(title="Test Service")
    
    @test_app.get("/test")
    async def test_endpoint():
        return {"message": "Test endpoint from dynamic router loader"}
    
    @test_app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "test_service"}
    
    return test_app


# Example usage and testing
if __name__ == "__main__":
    from fastapi import FastAPI
    
    # Create test app
    app = FastAPI(title="Router Loader Test")
    loader = DynamicRouterLoader()
    
    # Create and load test app
    test_config = RouterConfig(
        service_name="test_service",
        module_path="test_app",  # This would normally be a file path
        app_name="test_app",
        prefix="/test"
    )
    
    # For testing, we'll manually add the test app
    test_app = create_test_app()
    loader.loaded_apps["test_service"] = test_app
    app.mount("/test", test_app)
    
    print("Test app mounted successfully!")
    print(f"Status: {loader.get_status()}")