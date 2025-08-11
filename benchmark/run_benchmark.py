#!/usr/bin/env python3
"""
Advanced Benchmark Runner for FastAPI Gateway

This script provides comprehensive benchmarking capabilities with multiple
test scenarios, automatic results analysis, and detailed reporting.
Now includes dynamic API discovery and testing!
"""

import os
import sys
import subprocess
import json
import time
import requests
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import csv
import logging

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from benchmark.config import BENCHMARK_CONFIGS, TEST_ENDPOINTS, BenchmarkConfig
    from benchmark.generators.subapp_discovery import SubAppDiscovery
    from benchmark.generators.locust_generator import DynamicLocustGenerator
except ImportError as e:
    print(f"Warning: Could not import benchmark modules: {e}")
    BENCHMARK_CONFIGS = {}
    TEST_ENDPOINTS = {}
    class BenchmarkConfig:
        pass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class BenchmarkRunner:
    """
    Advanced class to run and manage API Gateway benchmarks with dynamic discovery
    """
    
    def __init__(self, host: str = "http://localhost:8000", enable_dynamic: bool = True):
        self.host = host
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(exist_ok=True)
        self.locust_file = Path(__file__).parent / "locustfile.py"
        
        # Dynamic discovery components
        self.enable_dynamic = enable_dynamic
        self.discovery = None
        self.dynamic_generator = None
        self.dynamic_locust_file = None
        
        if enable_dynamic:
            try:
                self.discovery = SubAppDiscovery(host)
                self.dynamic_generator = DynamicLocustGenerator(self.discovery)
                logger.info("Dynamic API discovery enabled")
            except Exception as e:
                logger.warning(f"Dynamic discovery initialization failed: {e}")
                self.enable_dynamic = False
        
    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        try:
            import locust
            import requests
            return True
        except ImportError as e:
            print(f"Missing dependency: {e}")
            print("Install with: pip install locust requests")
            return False
    
    def check_api_health(self) -> bool:
        """Check if the API is running and healthy"""
        try:
            response = requests.get(f"{self.host}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"API health check failed: {e}")
            return False
    
    def discover_apis(self) -> Dict[str, Any]:
        """Discover all available APIs and endpoints"""
        if not self.enable_dynamic or not self.discovery:
            return {"error": "Dynamic discovery not available"}
        
        try:
            logger.info("Starting API discovery...")
            
            # Discover all docs endpoints
            docs_info = self.discovery.discover_all_docs()
            logger.info(f"Discovered {len(docs_info)} documentation endpoints")
            
            # Extract all endpoints
            endpoints = self.discovery.extract_all_endpoints()
            logger.info(f"Discovered {len(endpoints)} API endpoints")
            
            # Get summary
            summary = self.discovery.get_app_summary()
            
            discovery_result = {
                "timestamp": datetime.now().isoformat(),
                "docs_endpoints": docs_info,
                "api_endpoints": endpoints,
                "summary": summary
            }
            
            # Save discovery results
            discovery_file = self.results_dir / f"api_discovery_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(discovery_file, 'w') as f:
                json.dump(discovery_result, f, indent=2)
            
            logger.info(f"Discovery results saved to: {discovery_file}")
            return discovery_result
            
        except Exception as e:
            logger.error(f"API discovery failed: {e}")
            return {"error": str(e)}
    
    def generate_dynamic_test_file(self) -> Optional[str]:
        """Generate dynamic locust test file based on discovered APIs"""
        if not self.enable_dynamic or not self.dynamic_generator:
            logger.warning("Dynamic generation not available")
            return None
        
        try:
            logger.info("Generating dynamic test file...")
            
            # Generate the dynamic locust file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_path = self.results_dir.parent / f"dynamic_locustfile_{timestamp}.py"
            
            generated_file = self.dynamic_generator.generate_dynamic_locust_file(str(output_path))
            self.dynamic_locust_file = generated_file
            
            logger.info(f"Dynamic test file generated: {generated_file}")
            return generated_file
            
        except Exception as e:
            logger.error(f"Failed to generate dynamic test file: {e}")
            return None
    
    def run_benchmark(self, 
                     test_type: str, 
                     users: Optional[int] = None, 
                     spawn_rate: Optional[int] = None, 
                     run_time: Optional[str] = None,
                     headless: bool = True,
                     use_dynamic: bool = True) -> Dict:
        """
        Run a benchmark test with optional dynamic discovery
        
        Args:
            test_type: Type of test (light, medium, heavy, dynamic, etc.)
            users: Number of users (overrides config)
            spawn_rate: Spawn rate (overrides config)
            run_time: Run time (overrides config)
            headless: Run in headless mode
            use_dynamic: Use dynamic test file if available
            
        Returns:
            Dict with benchmark results
        """
        
        # Determine which locust file to use
        locust_file_to_use = self.locust_file
        test_info = {"type": test_type, "dynamic": False}
        
        # Check if we should use dynamic testing
        if use_dynamic and test_type == "dynamic" and self.enable_dynamic:
            dynamic_file = self.generate_dynamic_test_file()
            if dynamic_file and os.path.exists(dynamic_file):
                locust_file_to_use = dynamic_file
                test_info["dynamic"] = True
                logger.info(f"Using dynamic test file: {dynamic_file}")
            else:
                logger.warning("Dynamic test file not available, falling back to static tests")
        
        # Get config for test type
        if test_type in BENCHMARK_CONFIGS:
            config = BENCHMARK_CONFIGS[test_type].copy()
        elif test_type == "dynamic":
            config = {
                "users": users or 20,
                "spawn_rate": spawn_rate or 3,
                "run_time": run_time or "120s",
                "host": self.host
            }
        else:
            config = {
                "users": users or 10,
                "spawn_rate": spawn_rate or 2,
                "run_time": run_time or "60s",
                "host": self.host
            }
        
        # Override with provided parameters
        if users is not None:
            config["users"] = users
        if spawn_rate is not None:
            config["spawn_rate"] = spawn_rate
        if run_time is not None:
            config["run_time"] = run_time
        
        # Generate result file names
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"benchmark_{test_type}_{timestamp}"
        html_file = self.results_dir / f"{base_filename}.html"
        csv_file = self.results_dir / f"{base_filename}.csv"
        
        print(f"🚀 Starting {test_type} benchmark...")
        print(f"   Test Mode: {'Dynamic' if test_info['dynamic'] else 'Static'}")
        print(f"   Users: {config['users']}")
        print(f"   Spawn Rate: {config['spawn_rate']}")
        print(f"   Duration: {config['run_time']}")
        print(f"   Host: {config['host']}")
        print(f"   Locust File: {Path(locust_file_to_use).name}")
        
        # Build locust command
        cmd = [
            "locust",
            "-f", str(locust_file_to_use),
            "--host", config['host'],
            "--users", str(config['users']),
            "--spawn-rate", str(config['spawn_rate']),
            "--run-time", config['run_time'],
            "--html", str(html_file),
            "--csv", str(csv_file)
        ]
        
        if headless:
            cmd.append("--headless")
        
        # Run the benchmark
        start_time = time.time()
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            end_time = time.time()
            
            success = result.returncode == 0
            
            benchmark_result = {
                "test_type": test_type,
                "config": config,
                "success": success,
                "duration": end_time - start_time,
                "timestamp": timestamp,
                "html_file": str(html_file) if success else None,
                "csv_file": str(csv_file) if success else None,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            if success:
                print(f"✅ Benchmark completed successfully!")
                print(f"   HTML Report: {html_file}")
                print(f"   CSV Data: {csv_file}")
                
                # Try to parse CSV results
                try:
                    stats = self.parse_csv_results(f"{csv_file}_stats.csv")
                    benchmark_result["stats"] = stats
                    print(f"   Total Requests: {stats.get('total_requests', 'N/A')}")
                    print(f"   Failed Requests: {stats.get('failed_requests', 'N/A')}")
                    print(f"   Average Response Time: {stats.get('avg_response_time', 'N/A')}ms")
                    print(f"   Requests/sec: {stats.get('requests_per_sec', 'N/A')}")
                except Exception as e:
                    print(f"   Could not parse CSV results: {e}")
                    
            else:
                print(f"❌ Benchmark failed!")
                print(f"   Error: {result.stderr}")
            
            return benchmark_result
            
        except Exception as e:
            print(f"❌ Failed to run benchmark: {e}")
            return {
                "test_type": test_type,
                "success": False,
                "error": str(e),
                "timestamp": timestamp
            }
    
    def parse_csv_results(self, csv_file_path: str) -> Dict:
        """Parse CSV results file and extract key metrics"""
        stats = {}
        
        if not os.path.exists(csv_file_path):
            return stats
        
        try:
            with open(csv_file_path, 'r') as f:
                reader = csv.DictReader(f)
                total_requests = 0
                total_failures = 0
                total_response_time = 0
                total_rps = 0
                
                for row in reader:
                    if row.get('Name') == 'Aggregated':
                        stats['total_requests'] = int(row.get('Request Count', 0))
                        stats['failed_requests'] = int(row.get('Failure Count', 0))
                        stats['avg_response_time'] = float(row.get('Average Response Time', 0))
                        stats['requests_per_sec'] = float(row.get('Requests/s', 0))
                        stats['min_response_time'] = float(row.get('Min Response Time', 0))
                        stats['max_response_time'] = float(row.get('Max Response Time', 0))
                        break
                        
        except Exception as e:
            print(f"Error parsing CSV: {e}")
        
        return stats
    
    def run_quick_test(self) -> bool:
        """Run a quick test to verify setup"""
        print("🔍 Running quick API test...")
        
        result = self.run_benchmark(
            test_type="quick",
            users=1,
            spawn_rate=1,
            run_time="10s",
            headless=True
        )
        
        return result.get("success", False)
    
    def run_test_suite(self, test_types: Optional[List[str]] = None) -> List[Dict]:
        """
        Run a suite of benchmark tests
        
        Args:
            test_types: List of test types to run (default: all available)
            
        Returns:
            List of benchmark results
        """
        if test_types is None:
            test_types = list(BENCHMARK_CONFIGS.keys())
        
        results = []
        
        print(f"🧪 Running test suite with {len(test_types)} tests...")
        
        for i, test_type in enumerate(test_types, 1):
            print(f"\n--- Test {i}/{len(test_types)}: {test_type} ---")
            
            result = self.run_benchmark(test_type)
            results.append(result)
            
            # Wait between tests
            if i < len(test_types):
                print("⏳ Waiting 10 seconds before next test...")
                time.sleep(10)
        
        print(f"\n🏁 Test suite completed! {len(results)} tests run.")
        return results


def main():
    """Main function for command line usage with dynamic discovery support"""
    parser = argparse.ArgumentParser(description="API Gateway Benchmark Runner with Dynamic Discovery")
    parser.add_argument("--host", default="http://localhost:8000", 
                       help="Target host URL")
    parser.add_argument("--test-type", choices=list(BENCHMARK_CONFIGS.keys()) + ["dynamic", "quick", "suite", "discover"],
                       default="light", help="Type of benchmark to run")
    parser.add_argument("--users", type=int, help="Number of users")
    parser.add_argument("--spawn-rate", type=int, help="Spawn rate")
    parser.add_argument("--run-time", help="Run time (e.g., 60s, 2m)")
    parser.add_argument("--check-health", action="store_true", 
                       help="Check API health before running")
    parser.add_argument("--interactive", action="store_true",
                       help="Run in interactive mode (web UI)")
    parser.add_argument("--disable-dynamic", action="store_true",
                       help="Disable dynamic API discovery")
    parser.add_argument("--discover-only", action="store_true",
                       help="Only run API discovery without benchmarking")
    
    args = parser.parse_args()
    
    # Create benchmark runner
    runner = BenchmarkRunner(host=args.host, enable_dynamic=not args.disable_dynamic)
    
    # Check dependencies
    if not runner.check_dependencies():
        return 1

    # Run discovery only if requested
    if args.discover_only or args.test_type == "discover":
        print("🔍 Running API discovery...")
        discovery_result = runner.discover_apis()
        if "error" in discovery_result:
            print(f"❌ Discovery failed: {discovery_result['error']}")
            return 1
        else:
            print("✅ API discovery completed successfully!")
            summary = discovery_result.get("summary", {})
            print(f"   📱 Apps found: {summary.get('total_apps', 0)}")
            print(f"   🔗 Endpoints found: {summary.get('total_endpoints', 0)}")
            return 0
    
    # Check API health if requested
    if args.check_health:
        if not runner.check_api_health():
            print("❌ API health check failed. Make sure the API is running.")
            return 1
        else:
            print("✅ API is healthy!")
    
    # Run appropriate test
    if args.test_type == "quick":
        success = runner.run_quick_test()
        return 0 if success else 1
    elif args.test_type == "suite":
        results = runner.run_test_suite()
        successful = sum(1 for r in results if r.get("success"))
        print(f"\nSuite Results: {successful}/{len(results)} tests passed")
        return 0 if successful == len(results) else 1
    else:
        use_dynamic = args.test_type == "dynamic" or (runner.enable_dynamic and not args.disable_dynamic)
        result = runner.run_benchmark(
            test_type=args.test_type,
            users=args.users,
            spawn_rate=args.spawn_rate,
            run_time=args.run_time,
            headless=not args.interactive,
            use_dynamic=use_dynamic
        )
        return 0 if result.get("success") else 1


if __name__ == "__main__":
    sys.exit(main())
