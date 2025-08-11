"""
Parameter Generator for Dynamic API Testing

This module generates appropriate test data for different parameter types
based on OpenAPI specifications, creating realistic test scenarios.
"""

import random
import string
from typing import Dict, List, Any, Union, Optional
from datetime import datetime, timedelta
import json
import uuid
import logging

logger = logging.getLogger(__name__)


class ParameterGenerator:
    """Generate appropriate test data for different parameter types"""
    
    def __init__(self):
        """Initialize the parameter generator"""
        self.context_patterns = self._build_context_patterns()
    
    def _build_context_patterns(self) -> Dict[str, Any]:
        """Build context-aware pattern generators"""
        return {
            'description': lambda: f"Test description for parameter",
            'title': lambda: f"Test Title {random.randint(1, 999)}",
            'content': lambda: f"Test content with random data {random.randint(1000, 9999)}",
            'message': lambda: f"Test message {random.randint(1, 999)}",
            'text': lambda: f"Sample text content {random.randint(1, 999)}",
            'query': lambda: f"test query {random.randint(1, 999)}",
            'search': lambda: f"search term {random.randint(1, 999)}",
            'filter': lambda: f"filter_{random.randint(1, 999)}",
            'tag': lambda: f"tag_{random.randint(1, 999)}",
            'category': lambda: random.choice(['test', 'sample', 'demo', 'example']),
            'status': lambda: random.choice(['active', 'inactive', 'pending', 'completed']),
            'type': lambda: random.choice(['type_a', 'type_b', 'default']),
            'code': lambda: f"CODE{random.randint(1000, 9999)}",
            'token': lambda: f"token_{uuid.uuid4().hex[:16]}",
            'key': lambda: f"key_{uuid.uuid4().hex[:12]}",
            'session': lambda: f"session_{uuid.uuid4().hex[:16]}"
        }
    
    def generate_for_parameter(self, param: Dict[str, Any]) -> Any:
        """
        Generate test value for a parameter based on its schema
        
        Args:
            param: Parameter definition from OpenAPI spec
            
        Returns:
            Generated test value
        """
        param_schema = param.get('schema', {})
        param_type = param_schema.get('type', 'string')
        param_name = param.get('name', '').lower()
        param_format = param_schema.get('format', '')
        
        logger.debug(f"Generating parameter for: {param_name} (type: {param_type}, format: {param_format})")
        
        # Handle by name patterns first (most specific)
        if 'id' in param_name:
            return self._generate_id_value(param_name, param_format)
        elif 'email' in param_name:
            return f"test{random.randint(1, 999)}@example.com"
        elif 'name' in param_name:
            return f"test_name_{random.randint(1, 999)}"
        elif 'date' in param_name:
            return (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat()
        elif param_name in ['limit', 'size']:
            return random.randint(1, 100)
        elif param_name in ['offset', 'skip']:
            return random.randint(0, 50)
        
        # Handle by type and format
        return self._generate_by_type(param_type, param_format, param_schema, param_name)
    
    def _generate_id_value(self, param_name: str, param_format: str) -> Union[str, int]:
        """Generate ID values based on format"""
        if 'uuid' in param_name or param_format == 'uuid':
            return str(uuid.uuid4())
        else:
            return random.randint(1, 1000)
    
    def _generate_by_type(self, param_type: str, param_format: str, 
                         schema: Dict[str, Any], param_name: str) -> Any:
        """Generate value by parameter type"""
        if param_type == 'string':
            return self._generate_string_value(param_format, schema, param_name)
        elif param_type == 'integer':
            return self._generate_integer_value(schema)
        elif param_type == 'number':
            return self._generate_number_value(schema)
        elif param_type == 'boolean':
            return random.choice([True, False])
        elif param_type == 'array':
            return self._generate_array_value(schema, param_name)
        else:
            return "test_value"  # Fallback
    
    def _generate_string_value(self, param_format: str, schema: Dict[str, Any], param_name: str) -> str:
        """Generate string values with format consideration"""
        if param_format == 'date-time':
            return datetime.now().isoformat()
        elif param_format == 'date':
            return datetime.now().date().isoformat()
        elif param_format == 'email':
            return f"test{random.randint(1, 999)}@example.com"
        elif param_format == 'uuid':
            return str(uuid.uuid4())
        elif param_format == 'password':
            return f"TestPass{random.randint(100, 999)}!"
        else:
            # Check for enum values
            enum_values = schema.get('enum', [])
            if enum_values:
                return random.choice(enum_values)
            
            # Generate based on parameter name context
            return self._generate_string_by_context(param_name)
    
    def _generate_integer_value(self, schema: Dict[str, Any]) -> int:
        """Generate integer values within constraints"""
        minimum = schema.get('minimum', 1)
        maximum = schema.get('maximum', 1000)
        return random.randint(minimum, maximum)
    
    def _generate_number_value(self, schema: Dict[str, Any]) -> float:
        """Generate number values within constraints"""
        minimum = schema.get('minimum', 0.1)
        maximum = schema.get('maximum', 999.9)
        return round(random.uniform(minimum, maximum), 2)
    
    def _generate_array_value(self, schema: Dict[str, Any], param_name: str) -> List[Any]:
        """Generate array values"""
        items_schema = schema.get('items', {})
        item_type = items_schema.get('type', 'string')
        array_size = random.randint(1, 3)
        
        if item_type == 'string':
            return [f"item_{i}_{random.randint(1, 99)}" for i in range(array_size)]
        elif item_type == 'integer':
            return [random.randint(1, 100) for _ in range(array_size)]
        else:
            return ["test_item"] * array_size
    
    def _generate_string_by_context(self, param_name: str) -> str:
        """Generate string value based on parameter name context"""
        name_lower = param_name.lower()
        
        for pattern, generator in self.context_patterns.items():
            if pattern in name_lower:
                return generator()
        
        # Default string generation
        return f"test_{param_name}_{random.randint(1, 999)}"
    
    def generate_request_body(self, request_body_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate request body based on schema
        
        Args:
            request_body_schema: Request body schema from OpenAPI spec
            
        Returns:
            Generated request body data
        """
        if not request_body_schema:
            return {}
        
        content = request_body_schema.get('content', {})
        
        # Try JSON content first
        json_content = content.get('application/json', {})
        if json_content:
            schema = json_content.get('schema', {})
            return self._generate_object_from_schema(schema)
        
        # Try form data
        form_content = content.get('application/x-www-form-urlencoded', {})
        if form_content:
            schema = form_content.get('schema', {})
            return self._generate_object_from_schema(schema)
        
        # Try multipart form (file uploads)
        multipart_content = content.get('multipart/form-data', {})
        if multipart_content:
            schema = multipart_content.get('schema', {})
            return self._generate_multipart_data(schema)
        
        return {}
    
    def _generate_object_from_schema(self, schema: Dict[str, Any]) -> Any:
        """Recursively generate object from JSON schema"""
        schema_type = schema.get('type', 'object')
        
        if schema_type == 'object':
            obj = {}
            properties = schema.get('properties', {})
            required = schema.get('required', [])
            
            for prop_name, prop_schema in properties.items():
                # Always include required properties, randomly include 70% of optional ones
                if prop_name in required or random.random() < 0.7:
                    obj[prop_name] = self._generate_value_from_schema(prop_name, prop_schema)
            return obj
        
        elif schema_type == 'array':
            items_schema = schema.get('items', {})
            array_size = random.randint(1, 3)
            return [
                self._generate_value_from_schema(f"item_{i}", items_schema)
                for i in range(array_size)
            ]
        
        else:
            return self._generate_value_from_schema('value', schema)
    
    def _generate_value_from_schema(self, name: str, schema: Dict[str, Any]) -> Any:
        """Generate a single value from schema"""
        schema_type = schema.get('type', 'string')
        schema_format = schema.get('format', '')
        
        # Handle by name patterns first
        name_lower = name.lower()
        if 'id' in name_lower:
            return self._generate_id_value(name_lower, schema_format)
        elif 'email' in name_lower:
            return f"test{random.randint(1, 999)}@example.com"
        elif 'password' in name_lower:
            return f"TestPass{random.randint(100, 999)}!"
        elif 'name' in name_lower:
            return f"Test {name.title().replace('_', ' ')} {random.randint(1, 999)}"
        
        # Handle by type
        return self._generate_by_type(schema_type, schema_format, schema, name)
    
    def _generate_multipart_data(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate multipart form data (for file uploads)"""
        data = {}
        properties = schema.get('properties', {})
        
        for prop_name, prop_schema in properties.items():
            prop_format = prop_schema.get('format', '')
            prop_type = prop_schema.get('type', 'string')
            
            if prop_format == 'binary' or 'file' in prop_name.lower():
                # Generate dummy file content
                data[prop_name] = ('test_file.txt', b'Test file content', 'text/plain')
            else:
                data[prop_name] = self._generate_value_from_schema(prop_name, prop_schema)
        
        return data
    
    def generate_realistic_data(self, endpoint_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate more realistic test data based on endpoint context
        
        Args:
            endpoint_info: Endpoint information including path, method, tags
            
        Returns:
            Context-aware test data
        """
        path = endpoint_info.get('path', '')
        method = endpoint_info.get('method', 'GET')
        tags = endpoint_info.get('tags', [])
        
        # Context-aware data generation
        context_data = {}
        
        if any(tag.lower() in ['user', 'account', 'profile'] for tag in tags):
            context_data.update({
                'user_id': random.randint(1, 1000),
                'username': f"testuser_{random.randint(1, 999)}",
                'email': f"user{random.randint(1, 999)}@example.com"
            })
        
        if any(tag.lower() in ['document', 'file'] for tag in tags):
            context_data.update({
                'filename': f"document_{random.randint(1, 999)}.txt",
                'file_size': random.randint(1024, 1048576),
                'content_type': random.choice(['text/plain', 'application/json', 'image/jpeg'])
            })
        
        if any(tag.lower() in ['session'] for tag in tags):
            context_data.update({
                'session_id': str(uuid.uuid4()),
                'session_name': f"test_session_{random.randint(1, 999)}"
            })
        
        return context_data


def main():
    """CLI for testing Parameter Generation"""
    # Test parameter generation
    test_parameters = [
        {
            'name': 'user_id',
            'in': 'path',
            'schema': {'type': 'integer', 'minimum': 1}
        },
        {
            'name': 'email',
            'in': 'query',
            'schema': {'type': 'string', 'format': 'email'}
        },
        {
            'name': 'limit',
            'in': 'query',
            'schema': {'type': 'integer', 'minimum': 1, 'maximum': 100}
        }
    ]
    
    generator = ParameterGenerator()
    
    print("🧪 Testing Parameter Generation:")
    for param in test_parameters:
        value = generator.generate_for_parameter(param)
        print(f"  {param['name']}: {value} (type: {type(value).__name__})")
    
    # Test request body generation
    test_request_body = {
        'content': {
            'application/json': {
                'schema': {
                    'type': 'object',
                    'properties': {
                        'name': {'type': 'string'},
                        'email': {'type': 'string', 'format': 'email'},
                        'age': {'type': 'integer', 'minimum': 18, 'maximum': 100},
                        'active': {'type': 'boolean'}
                    },
                    'required': ['name', 'email']
                }
            }
        }
    }
    
    print("\n🧪 Testing Request Body Generation:")
    body = generator.generate_request_body(test_request_body)
    print(f"  Generated body: {json.dumps(body, indent=2)}")


if __name__ == "__main__":
    main()
