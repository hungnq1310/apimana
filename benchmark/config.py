"""
Enhanced Configuration for API Gateway Benchmarking with Dynamic Discovery

This module contains all configuration settings for both static and
dynamic benchmarking scenarios.
"""

# Static Benchmark Configurations
BENCHMARK_CONFIGS = {
    "light": {
        "users": 5,
        "spawn_rate": 1,
        "run_time": "30s",
        "host": "http://localhost:8000",
        "description": "Light load test - basic functionality validation"
    },
    "medium": {
        "users": 20,
        "spawn_rate": 3,
        "run_time": "60s",
        "host": "http://localhost:8000",
        "description": "Medium load test - normal usage simulation"
    },
    "heavy": {
        "users": 50,
        "spawn_rate": 5,
        "run_time": "120s",
        "host": "http://localhost:8000",
        "description": "Heavy load test - high traffic simulation"
    },
    "spike": {
        "users": 100,
        "spawn_rate": 10,
        "run_time": "60s",
        "host": "http://localhost:8000",
        "description": "Spike test - sudden traffic burst"
    },
    "dynamic": {
        "users": 30,
        "spawn_rate": 4,
        "run_time": "90s",
        "host": "http://localhost:8000", 
        "description": "Dynamic test - auto-discovered endpoints"
    }
}

# Static Test Endpoints (Traditional)
TEST_ENDPOINTS = {
    "gateway": [
        {"path": "/", "method": "GET", "weight": 5, "name": "root"},
        {"path": "/health", "method": "GET", "weight": 10, "name": "health"},
        {"path": "/docs", "method": "GET", "weight": 3, "name": "docs"}
    ],
}

# Dynamic Discovery Configuration
DYNAMIC_CONFIG = {
    # Discovery settings
    "discovery_timeout": 30,           # seconds
    "max_retries": 3,                 # retry attempts for failed requests
    "docs_paths": [                   # documentation endpoint patterns
        "/docs/openapi.json",
        "/openapi.json", 
        "/redoc",
        "/docs"
    ],
    "subapp_prefixes": [              # common sub-app prefixes to check
        "/api",
        "/v1", 
        "/docman",
        "/auth",
        "/admin"
    ],
    
    # Endpoint filtering
    "max_endpoints_per_app": 50,      # limit endpoints per app
    "exclude_paths": [                # paths to exclude from testing
        "/docs",
        "/redoc", 
        "/openapi.json",
        "/favicon.ico",
        "/static",
        "/assets"
    ],
    "exclude_methods": [],            # methods to exclude (empty = include all)
    
    # Parameter generation
    "enable_parameter_inference": True,     # smart parameter generation
    "default_string_length": 10,           # default string parameter length
    "default_array_size": 3,               # default array size
    "file_upload_size": 1024,              # file upload size in bytes
    "max_request_body_size": 10240,        # max JSON body size in bytes
    
    # Test generation
    "generate_crud_sequences": True,        # generate CRUD operation sequences
    "include_error_scenarios": True,       # include error testing scenarios
    "enable_resource_cleanup": True,       # cleanup created resources
    "user_class_variants": [               # different user behavior patterns
        {"name": "LightUser", "weight": 3, "wait_time": (3, 7)},
        {"name": "MediumUser", "weight": 2, "wait_time": (1, 3)}, 
        {"name": "HeavyUser", "weight": 1, "wait_time": (0.1, 1)}
    ],
    
    # Response handling
    "acceptable_status_codes": {
        "GET": [200, 404, 403],           # 404 OK for non-existent test data
        "POST": [200, 201, 400, 409],     # 400/409 OK for validation errors  
        "PUT": [200, 204, 404, 400],      # 404 OK for non-existent resources
        "PATCH": [200, 204, 404, 400],    # similar to PUT
        "DELETE": [200, 204, 404]         # 404 OK for already deleted
    }
}

# Parameter Generation Patterns
PARAMETER_PATTERNS = {
    # ID patterns
    "id_patterns": {
        "uuid_fields": ["id", "session_id", "document_id", "user_id", "uuid"],
        "integer_fields": ["pk", "primary_key", "index"],
        "string_fields": ["code", "key", "token"]
    },
    
    # Data type patterns
    "field_patterns": {
        "email": ["email", "e_mail", "mail_address"],
        "url": ["url", "link", "href", "uri"],
        "phone": ["phone", "telephone", "mobile", "cell"],
        "name": ["name", "title", "label", "display_name"],
        "description": ["description", "desc", "summary", "note"],
        "date": ["date", "created_at", "updated_at", "timestamp"],
        "boolean": ["active", "enabled", "is_", "has_", "can_"]
    },
    
    # Value generators
    "generators": {
        "uuid": "str(uuid.uuid4())",
        "email": "f'test{random.randint(1, 999)}@example.com'",
        "url": "f'https://example.com/test/{random.randint(1, 999)}'",
        "phone": "f'+1-555-{random.randint(1000, 9999)}'",
        "name": "f'Test User {random.randint(1, 999)}'",
        "description": "f'Test description {random.randint(1, 999)}'",
        "date": "datetime.now().isoformat()",
        "boolean": "random.choice([True, False])"
    }
}

# Test data configuration (Enhanced)
TEST_DATA = {
    "file_sizes": {
        "small": 1024,      # 1KB
        "medium": 10240,    # 10KB
        "large": 102400,    # 100KB
        "xlarge": 1048576   # 1MB
    },
    "file_types": [
        "text/plain",
        "application/json",
        "text/csv",
        "application/pdf",
        "image/jpeg",
        "multipart/form-data"
    ]
}

# Benchmark Analysis Configuration
ANALYSIS_CONFIG = {
    "performance_targets": {
        "response_time_p95": 500,      # ms - 95th percentile response time
        "response_time_p99": 1000,     # ms - 99th percentile response time
        "error_rate_max": 1.0,         # % - maximum acceptable error rate
        "min_rps": 10,                 # requests per second minimum
        "availability_min": 99.0       # % - minimum availability
    },
    
    "alert_thresholds": {
        "response_time_critical": 2000,  # ms
        "error_rate_critical": 5.0,      # %
        "memory_usage_critical": 80.0,   # %
        "cpu_usage_critical": 80.0       # %
    },
    
    "report_sections": [
        "summary",
        "performance_metrics", 
        "error_analysis",
        "endpoint_breakdown",
        "recommendations"
    ]
}

# Load Testing Environments
ENVIRONMENTS = {
    "local": {
        "host": "http://localhost:8000",
        "description": "Local development environment"
    },
    "staging": {
        "host": "https://staging-api.example.com",
        "description": "Staging environment"
    },
    "production": {
        "host": "https://api.example.com", 
        "description": "Production environment (use with caution!)"
    }
}

# Integration Settings
INTEGRATION_CONFIG = {
    "export_formats": ["html", "csv", "json"],
    "webhook_notifications": False,
    "slack_notifications": False,
    "email_notifications": False,
    "ci_integration": True,
    "docker_support": True
}


# Utility Classes for Configuration Management
class BenchmarkConfig:
    """Configuration management class for benchmarks"""
    
    def __init__(self, config_name: str = "medium"):
        self.config_name = config_name
        self.config = BENCHMARK_CONFIGS.get(config_name, BENCHMARK_CONFIGS["medium"])
        self.dynamic_config = DYNAMIC_CONFIG
        
    def get_static_config(self):
        """Get static benchmark configuration"""
        return self.config.copy()
    
    def get_dynamic_config(self):
        """Get dynamic discovery configuration"""
        return self.dynamic_config.copy()
    
    def get_test_endpoints(self):
        """Get static test endpoints"""
        return TEST_ENDPOINTS.copy()
        
    def update_config(self, **kwargs):
        """Update configuration parameters"""
        self.config.update(kwargs)
    
    def get_parameter_patterns(self):
        """Get parameter generation patterns"""
        return PARAMETER_PATTERNS.copy()
    
    def get_analysis_config(self):
        """Get analysis configuration"""
        return ANALYSIS_CONFIG.copy()


class EnvironmentConfig:
    """Environment-specific configuration management"""
    
    def __init__(self, env_name: str = "local"):
        self.env_name = env_name
        self.env_config = ENVIRONMENTS.get(env_name, ENVIRONMENTS["local"])
    
    def get_host(self):
        """Get host URL for environment"""
        return self.env_config["host"]
    
    def get_description(self):
        """Get environment description"""
        return self.env_config["description"]
        
    @classmethod
    def list_environments(cls):
        """List all available environments"""
        return list(ENVIRONMENTS.keys())


# Export main configurations for easy imports
__all__ = [
    "BENCHMARK_CONFIGS",
    "TEST_ENDPOINTS", 
    "DYNAMIC_CONFIG",
    "PARAMETER_PATTERNS",
    "ANALYSIS_CONFIG",
    "ENVIRONMENTS",
    "BenchmarkConfig",
    "EnvironmentConfig"
]
