#!/usr/bin/env python3
"""
Test script to demonstrate dynamic discovery features

This script shows how to use the dynamic API discovery and testing
capabilities step by step.
"""

import sys
import json
import logging
from pathlib import Path
from datetime import datetime

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

from generators.subapp_discovery import SubAppDiscovery
from generators.parameter_generator import ParameterGenerator  
from generators.locust_generator import DynamicLocustGenerator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_discovery(host: str = "http://localhost:8000"):
    """Test API discovery functionality"""
    print("🔍 Testing API Discovery")
    print("=" * 50)
    
    try:
        # Initialize discovery
        discovery = SubAppDiscovery(host)
        
        # Step 1: Discover docs endpoints
        print("\n1. Discovering documentation endpoints...")
        docs_info = discovery.discover_all_docs()
        print(f"   Found {len(docs_info)} docs endpoints:")
        for app_name, doc_info in docs_info.items():
            print(f"     - {app_name}: {doc_info['docs_url']} (prefix: {doc_info['prefix']})")
        
        # Step 2: Extract endpoints
        print("\n2. Extracting API endpoints...")
        endpoints = discovery.extract_all_endpoints()
        print(f"   Found {len(endpoints)} API endpoints")
        
        # Show some examples
        if endpoints:
            print("   Examples:")
            for endpoint in endpoints[:5]:  # Show first 5
                print(f"     - {endpoint['method']} {endpoint['path']} ({endpoint['app']})")
        
        # Step 3: Get summary
        print("\n3. Discovery summary:")
        summary = discovery.get_app_summary()
        print(f"   Total apps: {summary.get('total_apps', 0)}")
        print(f"   Total endpoints: {summary.get('total_endpoints', 0)}")
        
        endpoints_by_method = summary.get('endpoints_by_method', {})
        if endpoints_by_method:
            print("   Endpoints by method:")
            for method, count in endpoints_by_method.items():
                print(f"     {method}: {count}")
        
        return discovery, endpoints
        
    except Exception as e:
        logger.error(f"Discovery failed: {e}")
        return None, []


def test_parameter_generation():
    """Test parameter generation functionality"""
    print("\n\n🎯 Testing Parameter Generation")
    print("=" * 50)
    
    try:
        generator = ParameterGenerator()
        
        # Test different parameter types
        test_cases = [
            {
                'name': 'session_id',
                'in': 'path',
                'schema': {'type': 'string', 'format': 'uuid'}
            },
            {
                'name': 'limit',
                'in': 'query',
                'schema': {'type': 'integer', 'minimum': 1, 'maximum': 100}
            },
            {
                'name': 'email',
                'in': 'query',
                'schema': {'type': 'string', 'format': 'email'}
            },
            {
                'name': 'user_name',
                'in': 'query', 
                'schema': {'type': 'string'}
            }
        ]
        
        print("\nParameter generation examples:")
        for i, param in enumerate(test_cases, 1):
            try:
                value = generator.generate_for_parameter(param)
                print(f"   {i}. {param['name']} ({param['schema']['type']}): {value}")
            except Exception as e:
                print(f"   {i}. {param['name']}: ERROR - {e}")
        
        # Test request body generation
        print("\nRequest body generation example:")
        sample_body_schema = {
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'name': {'type': 'string'},
                            'email': {'type': 'string', 'format': 'email'},
                            'age': {'type': 'integer', 'minimum': 18, 'maximum': 100}
                        },
                        'required': ['name', 'email']
                    }
                }
            }
        }
        
        body_data = generator.generate_request_body(sample_body_schema)
        print(f"   Generated body: {json.dumps(body_data, indent=2)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Parameter generation test failed: {e}")
        return False


def test_dynamic_generation(discovery, host: str = "http://localhost:8000"):
    """Test dynamic Locust file generation"""
    print("\n\n🧩 Testing Dynamic Test Generation")
    print("=" * 50)
    
    try:
        generator = DynamicLocustGenerator(discovery)
        
        # Generate dynamic test file
        print("\nGenerating dynamic test file...")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"test_dynamic_locustfile_{timestamp}.py"
        
        generated_file = generator.generate_dynamic_locust_file(output_file)
        
        if generated_file and Path(generated_file).exists():
            file_size = Path(generated_file).stat().st_size
            print(f"   ✅ Generated: {generated_file}")
            print(f"   📄 File size: {file_size} bytes")
            
            # Show first few lines
            print("\nFirst few lines of generated file:")
            with open(generated_file, 'r') as f:
                lines = f.readlines()[:10]
                for i, line in enumerate(lines, 1):
                    print(f"   {i:2d}: {line.rstrip()}")
            
            return generated_file
        else:
            print("   ❌ File generation failed")
            return None
            
    except Exception as e:
        logger.error(f"Dynamic generation test failed: {e}")
        return None


def test_full_workflow(host: str = "http://localhost:8000"):
    """Test the complete workflow"""
    print("🚀 Testing Complete Dynamic Discovery Workflow")
    print("=" * 60)
    
    # Step 1: Discovery
    discovery, endpoints = test_discovery(host)
    if not discovery:
        print("❌ Discovery failed - cannot continue")
        return False
    
    # Step 2: Parameter generation
    if not test_parameter_generation():
        print("❌ Parameter generation failed - continuing anyway")
    
    # Step 3: Dynamic test generation
    generated_file = test_dynamic_generation(discovery, host)
    if not generated_file:
        print("❌ Test generation failed")
        return False
    
    # Summary
    print("\n\n📊 Workflow Summary")
    print("=" * 50)
    print(f"   Host tested: {host}")
    print(f"   Discovery successful: ✅")
    print(f"   Endpoints found: {len(endpoints)}")
    print(f"   Test file generated: ✅")
    print(f"   Output file: {generated_file}")
    
    # Cleanup generated file
    try:
        Path(generated_file).unlink()
        print(f"   Cleaned up test file: {generated_file}")
    except:
        pass
    
    return True


def main():
    """Main test function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Dynamic Discovery Features")
    parser.add_argument("--host", default="http://localhost:8000", 
                       help="API host to test against")
    parser.add_argument("--test", choices=['discovery', 'parameters', 'generation', 'full'],
                       default='full', help="Which test to run")
    parser.add_argument("--verbose", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print("🧪 Dynamic Discovery Test Suite")
    print("=" * 60)
    print(f"Target host: {args.host}")
    print(f"Test mode: {args.test}")
    print("")
    
    try:
        if args.test == 'discovery':
            discovery, endpoints = test_discovery(args.host)
            success = discovery is not None
        elif args.test == 'parameters':
            success = test_parameter_generation()
        elif args.test == 'generation':
            discovery, _ = test_discovery(args.host)
            if discovery:
                generated_file = test_dynamic_generation(discovery, args.host)
                success = generated_file is not None
            else:
                success = False
        else:  # full
            success = test_full_workflow(args.host)
        
        if success:
            print("\n🎉 All tests completed successfully!")
            return 0
        else:
            print("\n❌ Some tests failed")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Test suite failed: {e}")
        print(f"\n💥 Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
