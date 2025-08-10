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
from fastapi import FastAPI, APIRouter

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class RouterConfig:
    """Configuration for a single router to be loaded"""
    service_name: str
    module_path: str
    router_name: str = "router"
    prefix: str = ""
    include_endpoints: Optional[Set[str]] = None
    exclude_endpoints: Optional[Set[str]] = None
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
        self.loaded_routers: Dict[str, APIRouter] = {}
        self.failed_loads: Dict[str, str] = {}
        self.router_configs: List[RouterConfig] = []
    
    def add_external_path(self, path: str) -> None:
        """Add external path to Python sys.path for imports"""
        if path not in sys.path:
            sys.path.insert(0, str(Path(path).resolve()))
            logger.info(f"Added path to sys.path: {path}")
    
    def load_router_from_path(self, config: RouterConfig) -> Optional[APIRouter]:
        """
        Load a router from the specified module path
        
        Args:
            config: RouterConfig containing load configuration
            
        Returns:
            APIRouter instance or None if loading fails
        """
        try:
            # Add external path if needed - handle special case for services with src/ structure
            module_path = Path(config.module_path)
            module_dir = module_path.parent
            
            # For services with src/ structure, add the root directory to path
            # This handles cases like external/docman/src/api/routes/documents.py
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
            
            # Get the router
            if hasattr(module, config.router_name):
                original_router = getattr(module, config.router_name)
                
                # Filter endpoints if specified
                if config.include_endpoints or config.exclude_endpoints:
                    filtered_router = self._filter_router_endpoints(
                        original_router, config
                    )
                    self.loaded_routers[config.service_name] = filtered_router
                    logger.info(
                        f"Successfully loaded and filtered router for {config.service_name}"
                    )
                    return filtered_router
                else:
                    self.loaded_routers[config.service_name] = original_router
                    logger.info(f"Successfully loaded router for {config.service_name}")
                    return original_router
            else:
                raise AttributeError(
                    f"Module {config.module_path} does not have attribute '{config.router_name}'"
                )
                
        except Exception as e:
            error_msg = f"Failed to load router for {config.service_name}: {str(e)}"
            logger.error(error_msg)
            self.failed_loads[config.service_name] = error_msg
            return None
    
    def _filter_router_endpoints(
        self, 
        original_router: APIRouter, 
        config: RouterConfig
    ) -> APIRouter:
        """
        Create a new router with filtered endpoints
        
        Args:
            original_router: The original router to filter
            config: RouterConfig with filtering rules
            
        Returns:
            New APIRouter with filtered endpoints
        """
        new_router = APIRouter(
            prefix=config.prefix
        )
        
        for route in original_router.routes:
            route_path = getattr(route, 'path', '')
            route_name = getattr(route, 'name', '')
            
            # Check if endpoint should be included
            should_include = True
            
            if config.include_endpoints:
                should_include = (
                    route_name in config.include_endpoints or
                    route_path in config.include_endpoints or
                    any(endpoint in route_path for endpoint in config.include_endpoints)
                )
            
            if config.exclude_endpoints and should_include:
                should_include = not (
                    route_name in config.exclude_endpoints or
                    route_path in config.exclude_endpoints or
                    any(endpoint in route_path for endpoint in config.exclude_endpoints)
                )
            
            if should_include:
                new_router.routes.append(route)
                logger.debug(f"Included endpoint: {route_path} ({route_name})")
            else:
                logger.debug(f"Excluded endpoint: {route_path} ({route_name})")
        
        return new_router
    
    def load_router(self, app: FastAPI, config: RouterConfig) -> bool:
        """
        Load and mount a single router to the FastAPI app
        
        Args:
            app: FastAPI application instance
            config: RouterConfig for the router to load
            
        Returns:
            bool: True if successful, False otherwise
        """
        router = self.load_router_from_path(config)
        if router:
            app.include_router(
                router,
                prefix=config.prefix
            )
            self.router_configs.append(config)
            logger.info(
                f"Mounted router for {config.service_name} "
                f"at prefix '{config.prefix}'"
            )
            return True
        return False
    
    def load_all_routers(
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
                success = self.load_router(app, config)
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
        """Get status information about loaded routers"""
        return {
            "loaded_routers": list(self.loaded_routers.keys()),
            "failed_loads": self.failed_loads,
            "total_loaded": len(self.loaded_routers),
            "total_failed": len(self.failed_loads)
        }
    
    def get_router(self, service_name: str) -> Optional[APIRouter]:
        """Get a loaded router by service name"""
        return self.loaded_routers.get(service_name)
    
    def reload_router(self, app: FastAPI, config: RouterConfig) -> bool:
        """
        Reload a specific router (useful for development)
        
        Args:
            app: FastAPI application instance
            config: RouterConfig for the router to reload
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Remove old router if exists
        if config.service_name in self.loaded_routers:
            del self.loaded_routers[config.service_name]
            
        # Clear failed loads for this service
        if config.service_name in self.failed_loads:
            del self.failed_loads[config.service_name]
        
        # Reload the router
        return self.load_router(app, config)


def create_test_router() -> APIRouter:
    """Create a test router for development/testing purposes"""
    test_router = APIRouter()
    
    @test_router.get("/test")
    async def test_endpoint():
        return {"message": "Test endpoint from dynamic router loader"}
    
    @test_router.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "test_service"}
    
    return test_router


# Example usage and testing
if __name__ == "__main__":
    from fastapi import FastAPI
    
    # Create test app
    app = FastAPI(title="Router Loader Test")
    loader = DynamicRouterLoader()
    
    # Create and load test router
    test_config = RouterConfig(
        service_name="test_service",
        module_path="test_router",  # This would normally be a file path
        router_name="test_router",
        prefix="/test"
    )
    
    # For testing, we'll manually add the test router
    test_router = create_test_router()
    loader.loaded_routers["test_service"] = test_router
    app.include_router(test_router, prefix="/test", tags=["Test"])
    
    print("Test router loaded successfully!")
    print(f"Status: {loader.get_status()}")
