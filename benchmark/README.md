# API Gateway Performance Benchmarking Suite

A comprehensive performance testing toolkit for FastAPI Gateway applications with **automatic API discovery** and dynamic test generation.

## ✨ Features

### Static Testing (Traditional)
- ✅ Pre-configured test scenarios (light, medium, heavy, spike loads)
- ✅ Multiple Locust user classes with different behaviors
- ✅ Detailed HTML and CSV reporting
- ✅ Health checks and API validation

### Dynamic Testing (Advanced)
- 🆕 **Auto-discovery** of FastAPI apps and endpoints
- 🆕 **Smart parameter generation** based on OpenAPI schemas
- 🆕 **Context-aware test data** (realistic IDs, emails, names)
- 🆕 **Multi-app support** with proper routing
- 🆕 **File upload testing** for multipart endpoints
- 🆕 **Session management** and resource cleanup

## 📁 Project Structure

```
benchmark/
├── config.py                   # Test configurations
├── locustfile.py              # Static Locust test scenarios
├── run_benchmark.py           # Main Python runner
├── run_benchmark.sh           # Shell script runner
├── test_dynamic.py            # Dynamic testing utilities
├── demo.sh                    # Interactive demo
├── requirements.txt           # Dependencies
├── generators/                # Test generators
│   ├── __init__.py
│   ├── locust_generator.py    # Dynamic Locust file generator
│   ├── parameter_generator.py # Smart parameter generation
│   └── subapp_discovery.py   # API discovery engine
├── utils/                     # Utilities
│   ├── __init__.py
│   └── analyze_results.py     # Results analysis
└── results/                   # Generated reports
    ├── *.html                 # Locust HTML reports
    ├── *.csv                  # Performance data
    ├── api_discovery_*.json   # Discovery results
    └── dynamic_locustfile_*.py # Generated test files
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Locust and requests
pip install -r benchmark/requirements.txt

# Or use the install script
./benchmark/run_benchmark.sh install
```

### 2. Start Your API

Make sure your API Gateway is running:

```bash
# From the root directory
python main.py
```

### 3. Run Benchmarks

```bash
# Quick health check
./benchmark/run_benchmark.sh health

# Static testing (traditional)
./benchmark/run_benchmark.sh light
./benchmark/run_benchmark.sh medium

# Dynamic discovery and testing
python benchmark/run_benchmark.py --test-type dynamic --users 20 --run-time 60s

# Discovery only (no testing)
python benchmark/run_benchmark.py --discover-only

# Interactive demo
cd benchmark && ./demo.sh
```

## 📊 Available Test Types

| Test Type | Users | Duration | Description |
|-----------|-------|----------|-------------|
| `light` | 5 | 60s | Basic functionality testing |
| `medium` | 20 | 120s | Moderate load testing |
| `heavy` | 50 | 300s | High load testing |
| `stress` | 100 | 600s | Stress testing |
| `spike` | 200 | 180s | Spike load testing |
| `dynamic` | Variable | Variable | Auto-discovery based testing |

## 🛠️ Usage Methods

### Method 1: Shell Script (Static Tests)

```bash
# Basic usage
./benchmark/run_benchmark.sh [TEST_TYPE] [--host URL]

# Examples
./benchmark/run_benchmark.sh light
./benchmark/run_benchmark.sh medium --host http://localhost:8080
./benchmark/run_benchmark.sh interactive  # Web UI at http://localhost:8089
```

### Method 2: Python Script (Static & Dynamic)

```bash
# Static testing
python benchmark/run_benchmark.py --test-type light
python benchmark/run_benchmark.py --test-type medium --users 30 --spawn-rate 5

# Dynamic testing
python benchmark/run_benchmark.py --test-type dynamic --users 20 --run-time 60s
python benchmark/run_benchmark.py --discover-only

# Test suite
python benchmark/run_benchmark.py --test-type suite
```

### Method 3: Direct Locust

```bash
# Interactive mode
locust -f benchmark/locustfile.py --host=http://localhost:8000

# Headless mode
locust -f benchmark/locustfile.py --host=http://localhost:8000 --users=10 --spawn-rate=2 --run-time=60s --headless

# Dynamic generated files
locust -f benchmark/results/dynamic_locustfile_*.py --host=http://localhost:8000 --headless
```

## 📈 Test Scenarios

The benchmarks test various API endpoints:

### Gateway Endpoints
- `GET /` - Root endpoint
- `GET /health` - Health check
- `GET /gateway/status` - Gateway status
- `GET /gateway/services` - Services listing

### Document Service Endpoints (if mounted)
- `GET /api/v1/documents/health` - Service health
- `GET /api/v1/documents/info` - Service info
- `POST /api/v1/documents/sessions` - Create session
- `POST /api/v1/documents/session/{id}/upload` - Upload document
- `GET /api/v1/documents/` - List documents

## 🔍 Dynamic API Discovery

### How It Works
The dynamic testing feature automatically:

1. **Discovers APIs**: Scans for FastAPI sub-apps and their `/docs` endpoints
2. **Extracts schemas**: Parses OpenAPI specifications for all endpoints
3. **Generates parameters**: Creates realistic test data based on parameter types
4. **Creates tests**: Builds complete Locust test files with proper error handling

### Example Discovery Output
```python
# Automatically discovered endpoints
{
    'main': {
        'prefix': '',
        'endpoints': ['/health', '/', '/gateway/status']
    },
    'docman': {
        'prefix': '/docman',
        'endpoints': ['/sessions', '/documents/{id}', '/chunks']
    }
}
```

### Smart Parameter Generation
```python
# Context-aware test data generation
{
    'session_id': 'uuid4()',           # UUID for ID fields
    'limit': 'random(1, 100)',        # Reasonable limits
    'email': 'test123@example.com',    # Valid email format
    'name': 'Test User 456',           # Human-readable names
    'file': 'BytesIO(b"test")'        # File uploads
}
```

## 📊 Understanding Results

### HTML Reports
After each test, an HTML report is generated with:
- Request statistics
- Response time graphs
- Failure analysis
- Charts and visualizations

### CSV Data
Raw data is saved in CSV format for further analysis:
- `*_stats.csv` - Request statistics
- `*_failures.csv` - Failure details
- `*_exceptions.csv` - Exception information

### Key Metrics
- **RPS** - Requests per second
- **Response Time** - Average/min/max response times
- **Failure Rate** - Percentage of failed requests
- **Throughput** - Data transfer rates

## 🔧 Configuration

### Custom Test Configuration

Edit `config.py` to modify test parameters:

```python
BENCHMARK_CONFIGS = {
    "custom": {
        "users": 25,
        "spawn_rate": 5,
        "run_time": "180s",
        "host": "http://localhost:8000",
        "description": "Custom test configuration"
    }
}

# Dynamic discovery settings
DYNAMIC_CONFIG = {
    "discovery_timeout": 30,
    "max_endpoints_per_app": 50,
    "enable_parameter_inference": True,
    "file_upload_size": 1024,  # bytes
}
```

### Environment Variables

```bash
export BENCHMARK_HOST="http://localhost:8080"
export BENCHMARK_USERS=50
export BENCHMARK_DURATION=300
```

## 📝 Custom Tests

### Creating Custom Locust Tasks

```python
from locust import HttpUser, task, between

class CustomUser(HttpUser):
    wait_time = between(1, 3)
    
    @task
    def custom_endpoint(self):
        self.client.get("/api/custom")
```

### Running Custom Tests

```bash
# Create your custom locust file
locust -f my_custom_test.py --host=http://localhost:8000
```

## 🐛 Troubleshooting

### Common Issues

1. **"Locust not found"**
   ```bash
   pip install locust
   ```

2. **"Connection refused"**
   - Make sure your API is running
   - Check the host URL
   - Verify the port number

3. **"Import errors"**
   - Install missing dependencies
   - Check Python path

### Discovery Issues
```bash
# Check if API is accessible
curl http://localhost:8000/health

# Check OpenAPI docs
curl http://localhost:8000/docs/openapi.json

# Run discovery with debug info
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from benchmark.generators.subapp_discovery import SubAppDiscovery
discovery = SubAppDiscovery('http://localhost:8000')
result = discovery.discover_all_docs()
print(result)
"
```

### Debug Mode

```bash
# Run with verbose output
python benchmark/run_benchmark.py --test-type light --check-health

# Check API status
./benchmark/run_benchmark.sh check

# Test parameter generation
python -c "
from benchmark.generators.parameter_generator import ParameterGenerator
gen = ParameterGenerator()
test_param = {'name': 'user_id', 'schema': {'type': 'integer'}}
print(gen.generate_for_parameter(test_param))
"
```

## 📊 Performance Analysis

### Interpreting Results

- **Good Performance**: RPS > 100, Response time < 200ms, Failure rate < 1%
- **Acceptable**: RPS > 50, Response time < 500ms, Failure rate < 5%
- **Poor**: RPS < 50, Response time > 1s, Failure rate > 10%

### Optimization Tips

1. **High Response Times**: Check database connections, caching
2. **High Failure Rates**: Check error logs, resource limits
3. **Low RPS**: Check CPU/memory usage, connection limits

## 🔗 Links

- [Locust Documentation](https://docs.locust.io/)
- [FastAPI Performance](https://fastapi.tiangolo.com/benchmarks/)
- [Load Testing Best Practices](https://docs.locust.io/en/stable/writing-a-locustfile.html)

## 📧 Support

For issues or questions about performance testing, check the logs in the `results/` directory or review the API Gateway logs.
