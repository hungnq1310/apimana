"""
Dynamic Locust Test Generator

This module generates Locust test files dynamically based on discovered
API endpoints and their parameters from OpenAPI specifications.
"""

import json
from typing import Dict, List, Any, Tuple
from datetime import datetime
from pathlib import Path
import logging

from .subapp_discovery import SubAppDiscovery
from .parameter_generator import ParameterGenerator

logger = logging.getLogger(__name__)


class DynamicLocustGenerator:
    """Generate Locust tests with proper parameter handling"""
    
    def __init__(self, subapp_discovery: SubAppDiscovery):
        """
        Initialize the generator
        
        Args:
            subapp_discovery: Configured SubAppDiscovery instance
        """
        self.discovery = subapp_discovery
        self.param_generator = ParameterGenerator()
    
    def generate_dynamic_locust_file(self, output_path: str = "benchmark/dynamic_locustfile.py") -> str:
        """
        Generate comprehensive Locust file with parameter handling
        
        Args:
            output_path: Path where to save the generated Locust file
            
        Returns:
            Path to the generated file
        """
        endpoints = self.discovery.extract_all_endpoints()
        
        if not endpoints:
            logger.warning("No endpoints discovered. Generating fallback test.")
            endpoints = self._generate_fallback_endpoints()
        
        locust_code = self._generate_full_locust_code(endpoints)
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(locust_code)
        
        logger.info(f"Generated dynamic Locust file: {output_file}")
        return str(output_file)
    
    def _generate_fallback_endpoints(self) -> List[Dict[str, Any]]:
        """Generate fallback endpoints when discovery fails"""
        return [
            {
                'app': 'main',
                'path': '/',
                'method': 'GET',
                'summary': 'Root endpoint',
                'tags': ['gateway'],
                'parameters': [],
                'request_body': {},
                'weight': 5
            },
            {
                'app': 'main',
                'path': '/health',
                'method': 'GET',
                'summary': 'Health check',
                'tags': ['health'],
                'parameters': [],
                'request_body': {},
                'weight': 5
            }
        ]
    
    def _generate_full_locust_code(self, endpoints: List[Dict[str, Any]]) -> str:
        """Generate the complete Locust Python code"""
        summary = self.discovery.get_app_summary()
        
        header = self._generate_header(endpoints, summary)
        imports = self._generate_imports()
        main_class = self._generate_main_class(endpoints)
        utility_methods = self._generate_utility_methods()
        user_classes = self._generate_user_classes()
        
        return f"{header}\n{imports}\n{main_class}\n{utility_methods}\n{user_classes}"
    
    def _generate_header(self, endpoints: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
        """Generate file header with documentation"""
        return f'''"""
Dynamic Locust file for multi-subapp FastAPI Gateway
Generated {len(endpoints)} endpoints across {summary['total_apps']} sub-apps
Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Apps discovered:
{self._format_apps_summary(summary)}

Endpoints by method:
{self._format_endpoints_summary(summary)}
"""'''
    
    def _generate_imports(self) -> str:
        """Generate necessary imports"""
        return '''
import random
import json
import uuid
import string
from datetime import datetime, timedelta
from io import BytesIO
from locust import HttpUser, task, between
import logging

logger = logging.getLogger(__name__)
'''
    
    def _generate_main_class(self, endpoints: List[Dict[str, Any]]) -> str:
        """Generate the main user class with all tasks"""
        class_header = '''
class DynamicAPIUser(HttpUser):
    wait_time = between(1, 3)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_data = {}
        self.created_resources = []
        self.auth_token = None
    
    def on_start(self):
        \"\"\"Initialize user session\"\"\"
        logger.info("Starting dynamic API user")
        self.session_data = {
            'user_id': random.randint(1, 1000),
            'session_id': str(uuid.uuid4())
        }
    
    def on_stop(self):
        \"\"\"Clean up when user stops\"\"\"
        self.cleanup_resources()
'''
        
        task_methods = self._generate_task_methods(endpoints)
        
        return f"{class_header}\n{task_methods}"
    
    def _format_apps_summary(self, summary: Dict[str, Any]) -> str:
        """Format apps summary for comment"""
        lines = []
        for app_name, app_info in summary.get('apps', {}).items():
            lines.append(f"  - {app_name}: {app_info['prefix']} ({app_info['paths_count']} paths)")
        return '\n'.join(lines) if lines else "  - No apps discovered"
    
    def _format_endpoints_summary(self, summary: Dict[str, Any]) -> str:
        """Format endpoints summary for comment"""
        lines = []
        for method, count in summary.get('endpoints_by_method', {}).items():
            lines.append(f"  - {method}: {count}")
        return '\n'.join(lines) if lines else "  - No endpoints discovered"
    
    def _generate_task_methods(self, endpoints: List[Dict[str, Any]]) -> str:
        """Generate task methods for all endpoints with proper parameter handling"""
        methods = []
        
        # Group endpoints by app for better organization
        endpoints_by_app = {}
        for endpoint in endpoints:
            app = endpoint['app']
            if app not in endpoints_by_app:
                endpoints_by_app[app] = []
            endpoints_by_app[app].append(endpoint)
        
        # Generate methods for each app
        for app_name, app_endpoints in endpoints_by_app.items():
            methods.append(f"\n    # {app_name.upper()} APP ENDPOINTS")
            methods.append(f"    # {'=' * 50}")
            
            for endpoint in app_endpoints:
                task_code = self._generate_task_code(endpoint)
                methods.append(task_code)
        
        return '\n'.join(methods)
    
    def _generate_task_code(self, endpoint: Dict[str, Any]) -> str:
        """Generate the actual task code for an endpoint"""
        method_name = self._generate_method_name(endpoint)
        weight = endpoint['weight']
        path = endpoint['path']
        http_method = endpoint['method'].lower()
        parameters = endpoint.get('parameters', [])
        request_body = endpoint.get('request_body', {})
        summary = endpoint.get('summary', path)
        app = endpoint['app']
        
        # Generate parameter handling code
        param_setup, param_usage = self._generate_parameter_code(parameters, request_body, path)
        
        # Generate response handling based on method
        response_handling = self._generate_response_handling(endpoint)
        
        return f'''
    @task({weight})
    def {method_name}(self):
        \"\"\"Test {summary} from {app} app\"\"\"
        try:
{param_setup}
            
            with self.client.{http_method}(
{param_usage}
                catch_response=True
            ) as response:
{response_handling}
        except Exception as e:
            logger.warning(f"Task {method_name} failed: {{e}}")
'''
    
    def _generate_method_name(self, endpoint: Dict[str, Any]) -> str:
        """Generate a valid Python method name from endpoint info"""
        path = endpoint['path']
        method = endpoint['method'].lower()
        app = endpoint['app']
        
        # Clean up path for method name
        path_clean = path.replace('/', '_').replace('{', '').replace('}', '')
        path_clean = ''.join(c for c in path_clean if c.isalnum() or c == '_')
        path_clean = path_clean.strip('_')
        
        if not path_clean:
            path_clean = 'root'
        
        method_name = f"test_{app}_{method}_{path_clean}"
        
        # Ensure method name is not too long and is valid
        method_name = method_name[:60]  # Limit length
        method_name = method_name.replace('__', '_')  # Remove double underscores
        
        return method_name
    
    def _generate_parameter_code(self, parameters: List[Dict], request_body: Dict, path: str) -> Tuple[str, str]:
        """Generate code to handle parameters and return setup and usage code"""
        setup_lines = [
            "            params = {}",
            "            json_data = None",
            "            files = None", 
            "            headers = {'Content-Type': 'application/json'}"
        ]
        
        path_params = {}
        
        # Handle parameters
        for param in parameters:
            param_name = param.get('name', '')
            param_in = param.get('in', '')
            
            if param_in == 'query':
                value_code = self._generate_parameter_value_code(param)
                setup_lines.append(f"            params['{param_name}'] = {value_code}")
            elif param_in == 'path':
                value_code = self._generate_parameter_value_code(param)
                setup_lines.append(f"            {param_name}_value = {value_code}")
                path_params[param_name] = f"{param_name}_value"
            elif param_in == 'header':
                value_code = self._generate_parameter_value_code(param)
                setup_lines.append(f"            headers['{param_name}'] = {value_code}")
        
        # Handle request body
        if request_body:
            body_code = self._generate_request_body_code(request_body)
            if 'multipart/form-data' in request_body.get('content', {}):
                setup_lines.append(f"            files = {body_code}")
                setup_lines.append("            headers.pop('Content-Type', None)  # Let requests set multipart boundary")
            else:
                setup_lines.append(f"            json_data = {body_code}")
        
        # Generate path with replacements
        final_path = path
        for param_name, param_var in path_params.items():
            final_path = final_path.replace(f"{{{param_name}}}", f"{{" + param_var + "}")
        
        if path_params:
            setup_lines.append(f"            final_path = f\"{final_path}\"")
            path_to_use = "final_path"
        else:
            path_to_use = f'"{final_path}"'
        
        # Usage code
        usage_lines = [
            f"                {path_to_use},",
            "                params=params if params else None,",
            "                json=json_data,",
            "                files=files,",
            "                headers=headers,"
        ]
        
        setup_code = '\n'.join(setup_lines)
        usage_code = '\n'.join(usage_lines)
        
        return setup_code, usage_code
    
    def _generate_parameter_value_code(self, param: Dict) -> str:
        """Generate code to create parameter value"""
        param_type = param.get('schema', {}).get('type', 'string')
        param_name = param.get('name', '').lower()
        param_format = param.get('schema', {}).get('format', '')
        
        if 'id' in param_name:
            if param_format == 'uuid' or 'uuid' in param_name:
                return "str(uuid.uuid4())"
            else:
                return "random.randint(1, 1000)"
        elif 'limit' in param_name or 'size' in param_name:
            return "random.randint(1, 100)"
        elif 'offset' in param_name:
            return "random.randint(0, 50)"
        elif param_type == 'integer':
            minimum = param.get('schema', {}).get('minimum', 1)
            maximum = param.get('schema', {}).get('maximum', 1000)
            return f"random.randint({minimum}, {maximum})"
        elif param_type == 'boolean':
            return "random.choice([True, False])"
        elif param_format == 'email':
            return f"f'test{{random.randint(1, 999)}}@example.com'"
        else:
            return f"f'test_{param_name}_{{random.randint(1, 999)}}'"
    
    def _generate_request_body_code(self, request_body: Dict) -> str:
        """Generate code for request body"""
        content = request_body.get('content', {})
        
        # Handle JSON content
        if 'application/json' in content:
            schema = content['application/json'].get('schema', {})
            return self._generate_json_body_code(schema)
        
        # Handle form data
        elif 'application/x-www-form-urlencoded' in content:
            schema = content['application/x-www-form-urlencoded'].get('schema', {})
            return self._generate_json_body_code(schema)  # Same as JSON for now
        
        # Handle multipart (file upload)
        elif 'multipart/form-data' in content:
            return self._generate_multipart_code()
        
        return "{}"
    
    def _generate_json_body_code(self, schema: Dict[str, Any]) -> str:
        """Generate JSON body code from schema"""
        if schema.get('type') == 'object':
            properties = schema.get('properties', {})
            required = schema.get('required', [])
            
            body_parts = []
            for prop_name, prop_schema in properties.items():
                if prop_name in required or len(body_parts) < 3:  # Include up to 3 properties
                    value_code = self._generate_schema_value_code(prop_name, prop_schema)
                    body_parts.append(f"'{prop_name}': {value_code}")
            
            return "{\n                " + ",\n                ".join(body_parts) + "\n            }"
        
        return "{}"
    
    def _generate_multipart_code(self) -> str:
        """Generate multipart form data code"""
        return '''{
                'file': ('test_file.txt', BytesIO(b'Test file content'), 'text/plain'),
                'description': f'Test upload {random.randint(1, 999)}'
            }'''
    
    def _generate_schema_value_code(self, prop_name: str, prop_schema: Dict[str, Any]) -> str:
        """Generate value code for a schema property"""
        prop_type = prop_schema.get('type', 'string')
        prop_format = prop_schema.get('format', '')
        
        name_lower = prop_name.lower()
        
        if 'id' in name_lower:
            if prop_format == 'uuid' or 'uuid' in name_lower:
                return "str(uuid.uuid4())"
            else:
                return "random.randint(1, 1000)"
        elif 'email' in name_lower:
            return "f'test{random.randint(1, 999)}@example.com'"
        elif 'name' in name_lower:
            return f"f'Test {prop_name.title()} {{random.randint(1, 999)}}'"
        elif 'description' in name_lower:
            return f"f'Test description for {prop_name} {{random.randint(1, 999)}}'"
        elif prop_type == 'string':
            if prop_format == 'date-time':
                return "datetime.now().isoformat()"
            elif prop_format == 'date':
                return "datetime.now().date().isoformat()"
            elif prop_format == 'email':
                return "f'test{random.randint(1, 999)}@example.com'"
            else:
                enum_values = prop_schema.get('enum', [])
                if enum_values:
                    return f"random.choice({enum_values})"
                return f"f'test_{prop_name}_{{random.randint(1, 999)}}'"
        elif prop_type == 'integer':
            minimum = prop_schema.get('minimum', 1)
            maximum = prop_schema.get('maximum', 1000)
            return f"random.randint({minimum}, {maximum})"
        elif prop_type == 'number':
            return "round(random.uniform(0.1, 999.9), 2)"
        elif prop_type == 'boolean':
            return "random.choice([True, False])"
        elif prop_type == 'array':
            return f"[f'item_{{i}}' for i in range(random.randint(1, 3))]"
        
        return f"f'test_{prop_name}_{{random.randint(1, 999)}}'"
    
    def _generate_response_handling(self, endpoint: Dict[str, Any]) -> str:
        """Generate response handling code based on endpoint"""
        method = endpoint['method']
        path = endpoint['path']
        
        # Different handling based on method
        if method == 'GET':
            return '''                if response.status_code == 200:
                    response.success()
                elif response.status_code == 404:
                    # 404 is acceptable for GET requests
                    response.success()
                elif response.status_code < 500:
                    response.success()
                else:
                    response.failure(f"Server error: {response.status_code}")'''
        
        elif method == 'POST':
            return '''                if response.status_code in [200, 201]:
                    response.success()
                    # Store created resource ID for potential cleanup
                    try:
                        data = response.json()
                        if isinstance(data, dict):
                            resource_id = data.get('id') or data.get('document_id') or data.get('session_id')
                            if resource_id:
                                self.created_resources.append(f"{path}/{resource_id}" if not str(resource_id) in path else path)
                    except:
                        pass
                elif response.status_code < 500:
                    response.success()  # Client errors are acceptable in testing
                else:
                    response.failure(f"Server error: {response.status_code}")'''
        
        elif method in ['PUT', 'PATCH']:
            return '''                if response.status_code in [200, 204]:
                    response.success()
                elif response.status_code == 404:
                    # Resource not found is acceptable
                    response.success()
                elif response.status_code < 500:
                    response.success()
                else:
                    response.failure(f"Server error: {response.status_code}")'''
        
        elif method == 'DELETE':
            return '''                if response.status_code in [200, 204, 404]:
                    response.success()  # 404 means already deleted
                elif response.status_code < 500:
                    response.success()
                else:
                    response.failure(f"Server error: {response.status_code}")'''
        
        else:
            return '''                if response.status_code < 500:
                    response.success()
                else:
                    response.failure(f"Server error: {response.status_code}")'''
    
    def _generate_utility_methods(self) -> str:
        """Generate utility methods for the user class"""
        return '''
    def cleanup_resources(self):
        \"\"\"Clean up any created resources\"\"\"
        for resource_path in self.created_resources:
            try:
                with self.client.delete(resource_path, catch_response=True) as response:
                    if response.status_code < 500:
                        logger.debug(f"Cleaned up resource: {resource_path}")
                    else:
                        logger.warning(f"Failed to cleanup {resource_path}: {response.status_code}")
            except Exception as e:
                logger.warning(f"Exception during cleanup of {resource_path}: {e}")
    
    def generate_test_file_content(self, size_bytes: int = 1024) -> bytes:
        \"\"\"Generate test file content for upload testing\"\"\"
        content = f"Test file generated at {datetime.now().isoformat()}\\n"
        content += "=" * 50 + "\\n"
        content += "This is test content for API benchmarking.\\n"
        
        # Pad to desired size
        while len(content.encode()) < size_bytes:
            content += f"Random data: {''.join(random.choices(string.ascii_letters + string.digits, k=50))}\\n"
        
        return content.encode()[:size_bytes]'''
    
    def _generate_user_classes(self) -> str:
        """Generate different user class variants"""
        return '''

class LightUser(DynamicAPIUser):
    \"\"\"Light load user with slower requests\"\"\"
    wait_time = between(3, 7)
    weight = 3


class MediumUser(DynamicAPIUser):
    \"\"\"Medium load user with normal timing\"\"\"
    wait_time = between(1, 3)
    weight = 2


class HeavyUser(DynamicAPIUser):
    \"\"\"Heavy load user with fast requests\"\"\"
    wait_time = between(0.1, 1)
    weight = 1


def main():
    \"\"\"CLI for testing the generator\"\"\"
    from .subapp_discovery import SubAppDiscovery
    
    # Test the generator
    discovery = SubAppDiscovery("http://localhost:8000")
    generator = DynamicLocustGenerator(discovery)
    
    output_file = generator.generate_dynamic_locust_file("test_dynamic_locustfile.py")
    print(f"Generated test file: {output_file}")


if __name__ == "__main__":
    main()
'''
