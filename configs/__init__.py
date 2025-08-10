"""
Configuration module for dynamic API Gateway.
Provides dynamic router loading and config management capabilities.
"""

from .router_loader import DynamicRouterLoader, RouterConfig, ROUTER_CONFIGS
from .config_manager import (
    DynamicConfigLoader,
    ConfigInjector, 
    UnifiedConfigManager
)

__all__ = [
    "DynamicRouterLoader",
    "RouterConfig", 
    "ROUTER_CONFIGS",
    "DynamicConfigLoader",
    "ConfigInjector",
    "UnifiedConfigManager"
]
