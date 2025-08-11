"""
SubApp Discovery System for FastAPI Multi-SubApp APIs

This module discovers all mounted sub-apps and their endpoints automatically
by analyzing OpenAPI specifications and testing common endpoint patterns.
"""

import requests
from typing import Dict, List, Set, Any, Optional
from urllib.parse import urljoin
import logging

logger = logging.getLogger(__name__)


class SubAppDiscovery:
    """Discover endpoints across multiple FastAPI sub-apps"""
    
    def __init__(self, base_url: str, timeout: int = 5):
        """
        Initialize the discovery system
        
        Args:
            base_url: The base URL of the FastAPI application
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.discovered_subapps = {}
        self.all_endpoints = set()
    
    def discover_all_docs(self) -> Dict[str, Any]:
        """Discover all documentation endpoints across sub-apps"""
        docs_endpoints = {}
        
        # First, discover mounted sub-apps
        subapp_prefixes = self._discover_subapp_prefixes()
        
        # Check main app docs
        main_docs = self._get_openapi_spec("/")
        if main_docs:
            docs_endpoints['main'] = {
                'prefix': '',
                'docs_url': '/docs',
                'openapi_url': '/openapi.json',
                'spec': main_docs
            }
        
        # Check each sub-app
        for prefix in subapp_prefixes:
            subapp_docs = self._get_openapi_spec(prefix + "/")
            if subapp_docs:
                service_name = prefix.strip('/').replace('/', '_') or 'root'
                docs_endpoints[service_name] = {
                    'prefix': prefix,
                    'docs_url': f'{prefix}/docs',
                    'openapi_url': f'{prefix}/openapi.json',
                    'spec': subapp_docs
                }
        
        return docs_endpoints
    
    def _discover_subapp_prefixes(self) -> Set[str]:
        """Discover mounted sub-app prefixes"""
        prefixes = set()
        
        # Try to get info from main gateway
        try:
            response = requests.get(f"{self.base_url}/gateway/services", timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                services = data.get('services', [])
                for service in services:
                    if isinstance(service, dict) and 'prefix' in service:
                        prefixes.add(service['prefix'])
                        logger.info(f"Discovered service prefix from gateway: {service['prefix']}")
        except Exception as e:
            logger.debug(f"Could not get services info: {e}")
        
        # Common sub-app patterns to try
        common_patterns = [
            '/api/v1', '/api/v2', '/api',
            '/admin', '/sessions',
            '/documents', '/docman',
            '/health', '/metrics', '/appv1'
        ]
        
        for pattern in common_patterns:
            if self._test_subapp_exists(pattern):
                prefixes.add(pattern)
                logger.info(f"Discovered sub-app at: {pattern}")
        
        return prefixes
    
    def _test_subapp_exists(self, prefix: str) -> bool:
        """Test if a sub-app exists at the given prefix"""
        test_endpoints = ['/docs', '/openapi.json', '/health', '/']
        
        for endpoint in test_endpoints:
            try:
                url = f"{self.base_url}{prefix}{endpoint}"
                response = requests.get(url, timeout=self.timeout)
                if response.status_code < 500:  # Any response except server error
                    logger.debug(f"Found sub-app endpoint: {url} -> {response.status_code}")
                    return True
            except Exception as e:
                logger.debug(f"Could not reach {url}: {e}")
                continue
        return False
    
    def _get_openapi_spec(self, prefix: str) -> Optional[Dict[str, Any]]:
        """Get OpenAPI spec for a specific app/sub-app"""
        openapi_paths = ['openapi.json', 'docs/openapi.json']
        
        for path in openapi_paths:
            try:
                url = f"{self.base_url}{prefix}{path}" if prefix else f"{self.base_url}/{path}"
                response = requests.get(url, timeout=self.timeout)
                if response.status_code == 200:
                    spec = response.json()
                    logger.info(f"Retrieved OpenAPI spec from: {url}")
                    return spec
            except Exception as e:
                logger.debug(f"Could not get OpenAPI spec from {url}: {e}")
        
        return None
    
    def extract_all_endpoints(self) -> List[Dict[str, Any]]:
        """Extract all endpoints from all discovered sub-apps"""
        all_endpoints = []
        docs_info = self.discover_all_docs()
        
        logger.info(f"Processing {len(docs_info)} apps for endpoint extraction")
        
        for app_name, app_info in docs_info.items():
            spec = app_info['spec']
            prefix = app_info['prefix']
            
            if 'paths' in spec:
                logger.info(f"Found {len(spec['paths'])} paths in {app_name}")
                for path, methods in spec['paths'].items():
                    full_path = f"{prefix}{path}" if prefix and not path.startswith(prefix) else path
                    
                    for method, details in methods.items():
                        if method.upper() in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                            endpoint_info = {
                                'app': app_name,
                                'path': full_path,
                                'method': method.upper(),
                                'summary': details.get('summary', ''),
                                'tags': details.get('tags', []),
                                'parameters': details.get('parameters', []),
                                'request_body': details.get('requestBody', {}),
                                'responses': details.get('responses', {}),
                                'weight': self._calculate_endpoint_weight(details, path)
                            }
                            all_endpoints.append(endpoint_info)
        
        logger.info(f"Total extracted endpoints: {len(all_endpoints)}")
        return all_endpoints
    
    def _calculate_endpoint_weight(self, details: Dict, path: str) -> int:
        """Calculate task weight based on endpoint characteristics"""
        path_lower = path.lower()
        
        # Health/status endpoints get higher weight (more frequent testing)
        if any(keyword in path_lower for keyword in ['health', 'status', 'ping']):
            return 5
        
        # Root endpoints
        if path in ('/', ''):
            return 4
        
        # GET endpoints are typically lighter/more frequent
        method = details.get('operationId', '').lower()
        if 'get' in method or not method:
            return 3
        
        # Documentation endpoints (less frequent)
        if any(keyword in path_lower for keyword in ['docs', 'openapi', 'swagger']):
            return 1
        
        # POST/PUT/DELETE are heavier but important
        return 2
    
    def get_app_summary(self) -> Dict[str, Any]:
        """Get a summary of discovered apps and endpoints"""
        docs_info = self.discover_all_docs()
        endpoints = self.extract_all_endpoints()
        
        summary = {
            'total_apps': len(docs_info),
            'total_endpoints': len(endpoints),
            'apps': {},
            'endpoints_by_method': {},
            'endpoints_by_app': {}
        }
        
        # Count endpoints by method
        for endpoint in endpoints:
            method = endpoint['method']
            summary['endpoints_by_method'][method] = summary['endpoints_by_method'].get(method, 0) + 1
        
        # Count endpoints by app
        for endpoint in endpoints:
            app = endpoint['app']
            summary['endpoints_by_app'][app] = summary['endpoints_by_app'].get(app, 0) + 1
        
        # App details
        for app_name, app_info in docs_info.items():
            summary['apps'][app_name] = {
                'prefix': app_info['prefix'],
                'docs_url': app_info['docs_url'],
                'paths_count': len(app_info['spec'].get('paths', {}))
            }
        
        return summary


def main():
    """CLI for testing SubApp Discovery"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test SubApp Discovery")
    parser.add_argument("--url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    print(f"🔍 Discovering API structure at {args.url}...")
    
    discovery = SubAppDiscovery(args.url)
    summary = discovery.get_app_summary()
    
    print(f"\n📊 Discovery Summary:")
    print(f"  Total Apps: {summary['total_apps']}")
    print(f"  Total Endpoints: {summary['total_endpoints']}")
    
    print(f"\n📚 Apps Found:")
    for app_name, app_info in summary['apps'].items():
        print(f"  - {app_name}: {app_info['prefix']} ({app_info['paths_count']} paths)")
    
    print(f"\n🎯 Endpoints by Method:")
    for method, count in summary['endpoints_by_method'].items():
        print(f"  - {method}: {count}")
    
    print(f"\n🏗️ Endpoints by App:")
    for app, count in summary['endpoints_by_app'].items():
        print(f"  - {app}: {count}")


if __name__ == "__main__":
    main()
