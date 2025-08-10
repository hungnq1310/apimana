"""
Main application file for Dynamic API Gateway

This file creates and configures the FastAPI application with dynamic
router loading and configuration management capabilities.
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from typing import Dict, Any
import sys
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from configs.router_loader import DynamicRouterLoader, ROUTER_CONFIGS
    from configs.config_manager import UnifiedConfigManager
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure FastAPI and other dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class APIGateway:
    """
    Main API Gateway class that orchestrates router loading and config management
    """
    
    def __init__(self, config_file: str = "gateway_config.yaml"):
        self.config_file = config_file
        self.config_manager = None
        self.router_loader = None
        self.app = None
        self.gateway_config = {}
        
    def initialize(self) -> FastAPI:
        """Initialize the API Gateway"""
        logger.info("Initializing API Gateway...")
        
        # Initialize configuration manager
        self.config_manager = UnifiedConfigManager(self.config_file)
        self.gateway_config = self.config_manager.get_gateway_config()
        
        # Create FastAPI application
        self.app = FastAPI(
            title=self.gateway_config.get("title", "Dynamic API Gateway"),
            description=self.gateway_config.get("description", "Gateway tích hợp 3 services với dynamic loading"),
            version=self.gateway_config.get("version", "1.0.0"),
            debug=self.gateway_config.get("debug", False)
        )
        
        # Setup CORS
        self._setup_cors()
        
        # Setup base routes
        self._setup_base_routes()
        
        # Initialize router loader
        self.router_loader = DynamicRouterLoader()
        
        # Setup configurations for all services
        self._setup_service_configurations()
        
        # Load and mount routers
        self._load_routers()
        
        logger.info("API Gateway initialization complete")
        return self.app
    
    def _setup_cors(self) -> None:
        """Setup CORS middleware"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        logger.info("CORS middleware configured")
    
    def _setup_base_routes(self) -> None:
        """Setup base routes for the gateway"""
        
        @self.app.get("/", tags=["Gateway"])
        async def root():
            """Root endpoint with gateway information"""
            return {
                "message": "Dynamic API Gateway",
                "version": self.gateway_config.get("version", "1.0.0"),
                "status": "running",
                "services": self.get_services_status()
            }
        
        @self.app.get("/health", tags=["Gateway"])
        async def health_check():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "gateway": "operational",
                "services": self.get_services_health()
            }
        
        @self.app.get("/gateway/status", tags=["Gateway"])
        async def gateway_status():
            """Detailed gateway status"""
            router_status = self.router_loader.get_status() if self.router_loader else {}
            config_status = self.config_manager.get_config_status() if self.config_manager else {}
            
            return {
                "gateway_config": self.gateway_config,
                "router_status": router_status,
                "config_status": config_status
            }
        
        @self.app.get("/gateway/services", tags=["Gateway"])
        async def list_services():
            """List all available services and their endpoints"""
            if not self.router_loader:
                return {"services": []}
            
            services = []
            for config in ROUTER_CONFIGS:
                service_info = {
                    "name": config.service_name,
                    "prefix": config.prefix,
                    "tags": config.tags,
                    "status": "loaded" if config.service_name in self.router_loader.loaded_routers else "failed"
                }
                
                if config.include_endpoints:
                    service_info["included_endpoints"] = list(config.include_endpoints)
                if config.exclude_endpoints:
                    service_info["excluded_endpoints"] = list(config.exclude_endpoints)
                
                services.append(service_info)
            
            return {"services": services}
        
        @self.app.post("/gateway/reload/{service_name}", tags=["Gateway"])
        async def reload_service(service_name: str):
            """Reload a specific service (development only)"""
            if not self.gateway_config.get("debug", False):
                raise HTTPException(status_code=403, detail="Reload only available in debug mode")
            
            if not self.router_loader:
                raise HTTPException(status_code=500, detail="Router loader not initialized")
            
            # Find the service config
            service_config = None
            for config in ROUTER_CONFIGS:
                if config.service_name == service_name:
                    service_config = config
                    break
            
            if not service_config:
                raise HTTPException(status_code=404, detail=f"Service {service_name} not found")
            
            # Reload the service
            success = self.router_loader.reload_router(self.app, service_config)
            if success:
                return {"message": f"Service {service_name} reloaded successfully"}
            else:
                raise HTTPException(status_code=500, detail=f"Failed to reload service {service_name}")
    
    def _setup_service_configurations(self) -> None:
        """Setup configurations for all services"""
        logger.info("Setting up service configurations...")
        
        try:
            # Setup configs for services that have config names
            configured_services = []
            for config in ROUTER_CONFIGS:
                if config.config_name:
                    try:
                        self.config_manager.setup_service_config(config.config_name)
                        configured_services.append(config.config_name)
                        logger.info(f"Configuration setup successful for {config.config_name}")
                    except Exception as e:
                        logger.error(f"Failed to setup config for {config.config_name}: {e}")
            
            logger.info(f"Service configurations complete: {configured_services}")
        
        except Exception as e:
            logger.error(f"Error during service configuration setup: {e}")
    
    def _load_routers(self) -> None:
        """Load and mount all routers"""
        logger.info("Loading routers...")
        
        try:
            # Load all routers
            results = self.router_loader.load_all_routers(self.app, ROUTER_CONFIGS)
            
            # Log results
            successful = [name for name, success in results.items() if success]
            failed = [name for name, success in results.items() if not success]
            
            if successful:
                logger.info(f"Successfully loaded routers: {successful}")
            if failed:
                logger.warning(f"Failed to load routers: {failed}")
            
        except Exception as e:
            logger.error(f"Error during router loading: {e}")
    
    def get_services_status(self) -> Dict[str, str]:
        """Get status of all services"""
        if not self.router_loader:
            return {}
        
        status = {}
        for config in ROUTER_CONFIGS:
            if config.service_name in self.router_loader.loaded_routers:
                status[config.service_name] = "loaded"
            elif config.service_name in self.router_loader.failed_loads:
                status[config.service_name] = "failed"
            else:
                status[config.service_name] = "unknown"
        
        return status
    
    def get_services_health(self) -> Dict[str, str]:
        """Get health status of all services"""
        # This is a simple implementation
        # In production, you might want to actually ping the services
        services_status = self.get_services_status()
        
        health = {}
        for service_name, status in services_status.items():
            health[service_name] = "healthy" if status == "loaded" else "unhealthy"
        
        return health


# Global gateway instance
gateway = APIGateway()


def create_app() -> FastAPI:
    """Factory function to create the FastAPI app"""
    return gateway.initialize()


def run_development_server() -> None:
    """Run the development server"""
    app = create_app()
    config = gateway.gateway_config
    
    uvicorn.run(
        app,
        host=config.get("host", "0.0.0.0"),
        port=config.get("port", 8000),
        reload=config.get("debug", False),
        log_level="info" if not config.get("debug", False) else "debug"
    )


# Error handlers
@gateway.app.exception_handler(404) if gateway.app else None
async def not_found_handler(request, exc):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url.path)
        }
    )


@gateway.app.exception_handler(500) if gateway.app else None
async def server_error_handler(request, exc):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An internal server error occurred"
        }
    )


if __name__ == "__main__":
    try:
        logger.info("Starting Dynamic API Gateway...")
        run_development_server()
    except KeyboardInterrupt:
        logger.info("Gateway stopped by user")
    except Exception as e:
        logger.error(f"Failed to start gateway: {e}")
        sys.exit(1)
