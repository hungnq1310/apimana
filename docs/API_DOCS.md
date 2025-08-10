# API Gateway Documentation

## Overview

The Dynamic API Gateway is a FastAPI-based application that dynamically loads and manages multiple service APIs. It provides unified access to different microservices through a single entry point with selective endpoint exposure and dynamic configuration management.

## Architecture

### Core Components

1. **Dynamic Router Loader** (`configs/router_loader.py`)
   - Dynamically loads routers from external services
   - Supports selective endpoint inclusion/exclusion
   - Handles router filtering and mounting

2. **Configuration Manager** (`configs/config_manager.py`)
   - Manages configurations for multiple services
   - Supports YAML file and environment variable configuration
   - Provides configuration injection and validation

3. **Main Application** (`main.py`)
   - Orchestrates the gateway initialization
   - Provides gateway management endpoints
   - Handles error handling and middleware setup

## API Endpoints

### Gateway Management Endpoints

#### GET /
- **Description**: Root endpoint with gateway information
- **Response**: Gateway status and services information
```json
{
  "message": "Dynamic API Gateway",
  "version": "1.0.0",
  "status": "running",
  "services": {
    "user_service": "loaded",
    "product_service": "loaded",
    "order_service": "failed"
  }
}
```

#### GET /health
- **Description**: Health check endpoint
- **Response**: Gateway and services health status
```json
{
  "status": "healthy",
  "gateway": "operational",
  "services": {
    "user_service": "healthy",
    "product_service": "healthy",
    "order_service": "unhealthy"
  }
}
```

#### GET /gateway/status
- **Description**: Detailed gateway status information
- **Response**: Comprehensive status including configurations
```json
{
  "gateway_config": {
    "host": "0.0.0.0",
    "port": 8000,
    "debug": true,
    "title": "Dynamic API Gateway"
  },
  "router_status": {
    "loaded_routers": ["user_service", "product_service"],
    "failed_loads": {"order_service": "Module not found"},
    "total_loaded": 2,
    "total_failed": 1
  },
  "config_status": {
    "loaded_services": ["user_service", "product_service"],
    "total_services": 2
  }
}
```

#### GET /gateway/services
- **Description**: List all available services and their configurations
- **Response**: Service information and endpoint details
```json
{
  "services": [
    {
      "name": "user_service",
      "prefix": "/api/v1/users",
      "tags": ["User Service"],
      "status": "loaded",
      "included_endpoints": ["/users", "/auth", "/profile"]
    },
    {
      "name": "product_service",
      "prefix": "/api/v1/products", 
      "tags": ["Product Service"],
      "status": "loaded",
      "excluded_endpoints": ["/admin"]
    }
  ]
}
```

#### POST /gateway/reload/{service_name}
- **Description**: Reload a specific service (development mode only)
- **Parameters**: 
  - `service_name` (path): Name of the service to reload
- **Requirements**: Gateway must be in debug mode
- **Response**: Reload status
```json
{
  "message": "Service user_service reloaded successfully"
}
```

### Service-Specific Endpoints

Service endpoints are mounted at their configured prefixes:

- **User Service**: `/api/v1/users/*`
- **Product Service**: `/api/v1/products/*`
- **Order Service**: `/api/v1/orders/*`

The actual endpoints depend on the loaded services and their configurations.

## Configuration

### Gateway Configuration

The main gateway configuration is defined in `gateway_config.yaml`:

```yaml
gateway:
  host: "0.0.0.0"
  port: 8000
  debug: true
  title: "Unified API Gateway"
  version: "1.0.0"
  description: "Gateway tích hợp 3 services với dynamic loading"
```

### Service Configuration

Each service can have its own configuration section:

```yaml
services:
  user_service:
    database_url: "postgresql://localhost/gateway_users"
    redis_url: "redis://localhost:6379/1" 
    jwt_secret: "user-jwt-secret"
    log_level: "DEBUG"
    
  product_service:
    database_url: "postgresql://localhost/gateway_products"
    elasticsearch_url: "http://localhost:9200"
    cache_ttl: 300
    log_level: "INFO"
```

### Environment Variables

Configuration can be overridden using environment variables:

```bash
# Gateway settings
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8000
GATEWAY_DEBUG=true

# Service-specific settings
USER_SERVICE_DATABASE_URL=postgresql://localhost/gateway_users
USER_SERVICE_JWT_SECRET=your-secret-key

PRODUCT_SERVICE_DATABASE_URL=postgresql://localhost/gateway_products
PRODUCT_SERVICE_CACHE_TTL=600
```

### Router Configuration

Router loading is configured in `configs/router_loader.py`:

```python
ROUTER_CONFIGS = [
    RouterConfig(
        service_name="user_service",
        module_path="external/user-service/app/main.py",
        router_name="router",
        prefix="/api/v1/users",
        tags=["User Service"],
        include_endpoints={"/users", "/auth", "/profile"},
        config_name="user_service"
    )
]
```

#### RouterConfig Parameters

- `service_name`: Unique identifier for the service
- `module_path`: Path to the module containing the router
- `router_name`: Name of the router variable in the module
- `prefix`: URL prefix for the service endpoints
- `tags`: OpenAPI tags for the service
- `include_endpoints`: Set of endpoints to include (optional)
- `exclude_endpoints`: Set of endpoints to exclude (optional)
- `config_name`: Configuration section name (optional)

## Running the Gateway

### Development Mode

```bash
# Install dependencies
pip install -r requirements.txt

# Run in development mode
python main.py
```

### Production Mode

```bash
# Using uvicorn directly
uvicorn main:create_app --host 0.0.0.0 --port 8000

# Using gunicorn (recommended for production)
gunicorn main:create_app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:create_app", "--host", "0.0.0.0", "--port", "8000"]
```

## Error Handling

The gateway provides comprehensive error handling:

### HTTP Error Codes

- `404`: Endpoint not found
- `500`: Internal server error
- `403`: Forbidden (e.g., reload in production mode)

### Error Response Format

```json
{
  "error": "Error Type",
  "message": "Detailed error message",
  "path": "/requested/path"
}
```

## Logging

The gateway uses Python's standard logging module:

```python
import logging

# Configure logging level
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

Log levels can be configured per service through the configuration files.

## Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=configs --cov=main

# Run specific test file
pytest tests/test_router_loader.py -v
```

### Test Structure

- `tests/test_router_loader.py`: Tests for dynamic router loading
- `tests/test_config_manager.py`: Tests for configuration management
- Integration tests for the complete gateway

## Monitoring and Health Checks

### Health Check Endpoints

- `GET /health`: Basic health check
- `GET /gateway/status`: Detailed status information

### Metrics

The gateway can be extended with metrics collection:

```python
from prometheus_client import Counter, Histogram

# Request counter
request_count = Counter('gateway_requests_total', 'Total requests')

# Response time histogram
response_time = Histogram('gateway_response_time_seconds', 'Response time')
```

## Security Considerations

### CORS Configuration

CORS is configured to allow all origins in development. For production:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
```

### Authentication

Individual services handle their own authentication. The gateway can be extended with:

- API key validation
- JWT token verification
- Rate limiting
- Request/response transformation

## Troubleshooting

### Common Issues

1. **Service fails to load**
   - Check module path in RouterConfig
   - Verify router name exists in module
   - Check Python path configuration

2. **Configuration not applied**
   - Verify YAML syntax
   - Check environment variable naming
   - Ensure config file exists

3. **Endpoints not accessible**
   - Check router prefix configuration
   - Verify endpoint filtering rules
   - Check service status via `/gateway/status`

### Debug Mode

Enable debug mode for detailed logging:

```yaml
gateway:
  debug: true
```

Or set environment variable:

```bash
GATEWAY_DEBUG=true
```

### Logs Analysis

Key log messages to look for:

- Router loading: `Successfully loaded router for {service_name}`
- Config setup: `Configuration setup successful for {service_name}`
- Errors: `Failed to load router for {service_name}: {error}`

## API Documentation

When the gateway is running, visit:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

These provide interactive documentation for all loaded service endpoints.
