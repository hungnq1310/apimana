#!/bin/bash
"""
Enhanced Demo script for API Gateway Benchmarking with Dynamic Discovery

This script demonstrates all benchmarking features including:
- Static endpoint testing
- Dynamic API discovery 
- Comprehensive test suites
- Results analysis
"""

set -e  # Exit on any error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HOST="http://localhost:8000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if API is running
check_api() {
    log_info "Checking if API Gateway is running..."
    if curl -s "$HOST/health" > /dev/null 2>&1; then
        log_success "API Gateway is running at $HOST"
        return 0
    else
        log_error "API Gateway is not running at $HOST"
        log_info "Please start the API Gateway first:"
        log_info "  cd /home/tiennv/hungnq/apimana"
        log_info "  python main.py"
        return 1
    fi
}

# Function to install dependencies
install_deps() {
    log_info "Installing benchmark dependencies..."
    cd "$SCRIPT_DIR"
    
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
        log_success "Dependencies installed successfully"
    else
        log_warning "requirements.txt not found, installing basic packages"
        pip install locust requests beautifulsoup4
    fi
}

# Function to discover APIs
discover_apis() {
    log_info "🔍 Running API discovery..."
    echo "=================================================="
    
    cd "$SCRIPT_DIR"
    python run_benchmark.py --host "$HOST" --discover-only
    
    if [[ $? -eq 0 ]]; then
        log_success "API discovery completed successfully!"
    else
        log_error "API discovery failed"
        return 1
    fi
    
    echo ""
    sleep 2
}

# Function to generate dynamic test file
generate_dynamic_tests() {
    log_info "🧩 Generating dynamic test file..."
    echo "=================================================="
    
    cd "$SCRIPT_DIR"
    python -c "
from subapp_discovery import SubAppDiscovery
from dynamic_locust_generator import DynamicLocustGenerator

discovery = SubAppDiscovery('$HOST')
generator = DynamicLocustGenerator(discovery)
output_file = generator.generate_dynamic_locust_file('demo_dynamic_locustfile.py')
print(f'Generated dynamic test file: {output_file}')
"
    
    if [[ $? -eq 0 ]]; then
        log_success "Dynamic test file generated successfully!"
    else
        log_warning "Dynamic test generation failed, continuing with static tests"
    fi
    
    echo ""
    sleep 2
}

# Function to run individual benchmark
run_benchmark() {
    local test_type=$1
    local description=$2
    
    log_info "🚀 Running $description..."
    echo "=================================================="
    
    cd "$SCRIPT_DIR"
    python run_benchmark.py --host "$HOST" --test-type "$test_type" --check-health
    
    if [[ $? -eq 0 ]]; then
        log_success "$description completed successfully!"
    else
        log_error "$description failed"
    fi
    
    echo ""
    log_info "Waiting 5 seconds before next test..."
    sleep 5
}

# Function to show results
show_results() {
    log_info "📊 Benchmark Results Summary"
    echo "=================================================="
    
    cd "$SCRIPT_DIR/results"
    
    # Count result files
    html_files=$(find . -name "*.html" -type f | wc -l)
    csv_files=$(find . -name "*.csv" -type f | wc -l)
    json_files=$(find . -name "*.json" -type f | wc -l)
    
    log_info "Generated files:"
    log_info "  📄 HTML Reports: $html_files"
    log_info "  📊 CSV Data: $csv_files" 
    log_info "  🔍 Discovery Data: $json_files"
    
    # Show latest HTML report
    latest_html=$(find . -name "*.html" -type f -printf '%T@ %p
' | sort -n | tail -1 | cut -d' ' -f2-)
    if [[ -n "$latest_html" ]]; then
        log_info "Latest HTML report: $latest_html"
        log_info "Open in browser: file://$SCRIPT_DIR/results/$latest_html"
    fi
    
    # Show discovery results if available
    latest_discovery=$(find . -name "api_discovery_*.json" -type f -printf '%T@ %p
' | sort -n | tail -1 | cut -d' ' -f2-)
    if [[ -n "$latest_discovery" ]]; then
        log_info "Latest API discovery: $latest_discovery"
        
        # Show summary from discovery file
        python -c "
import json
try:
    with open('$latest_discovery', 'r') as f:
        data = json.load(f)
        summary = data.get('summary', {})
        print(f'  📱 Apps discovered: {summary.get("total_apps", 0)}')
        print(f'  🔗 Total endpoints: {summary.get("total_endpoints", 0)}')
        
        endpoints_by_method = summary.get('endpoints_by_method', {})
        for method, count in endpoints_by_method.items():
            print(f'  {method}: {count}')
except Exception as e:
    print(f'  Could not parse discovery file: {e}')
"
    fi
    
    echo ""
}

# Main execution
main() {
    log_info "🎯 API Gateway Benchmark Demo with Dynamic Discovery"
    log_info "=================================================="
    echo ""
    
    # Check if API is running
    if ! check_api; then
        exit 1
    fi
    
    echo ""
    
    # Install dependencies
    install_deps
    echo ""
    
    # Create results directory
    mkdir -p "$SCRIPT_DIR/results"
    
    # Discover APIs first
    discover_apis
    
    # Generate dynamic tests
    generate_dynamic_tests
    
    # Run benchmarks
    log_info "🧪 Starting comprehensive benchmark suite..."
    echo ""
    
    # 1. API Discovery Test
    run_benchmark "discover" "API Discovery Benchmark"
    
    # 2. Dynamic Test (using discovered endpoints)
    run_benchmark "dynamic" "Dynamic API Testing (auto-discovered endpoints)"
    
    # 3. Static Tests for comparison  
    run_benchmark "light" "Light Load Test (static endpoints)"
    run_benchmark "medium" "Medium Load Test (static endpoints)"
    
    # 4. Quick health test
    run_benchmark "quick" "Quick Health Check"
    
    # Show final results
    show_results
    
    log_success "🏁 Demo completed successfully!"
    log_info "Check the results directory for detailed reports"
    log_info "Results location: $SCRIPT_DIR/results/"
}

# Help function
show_help() {
    echo "Enhanced API Gateway Benchmark Demo"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --host URL       Set the API host (default: http://localhost:8000)"
    echo "  --discover-only  Only run API discovery"
    echo "  --dynamic-only   Only run dynamic tests"
    echo "  --static-only    Only run static tests"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                           # Run full demo"
    echo "  $0 --discover-only          # Only discover APIs"
    echo "  $0 --dynamic-only           # Only test discovered endpoints"
    echo "  $0 --host http://prod:8080  # Test different host"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --host)
            HOST="$2"
            shift 2
            ;;
        --discover-only)
            DISCOVER_ONLY=1
            shift
            ;;
        --dynamic-only)
            DYNAMIC_ONLY=1
            shift
            ;;
        --static-only)
            STATIC_ONLY=1
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Execute based on options
if [[ $DISCOVER_ONLY -eq 1 ]]; then
    check_api && install_deps && discover_apis
elif [[ $DYNAMIC_ONLY -eq 1 ]]; then
    check_api && install_deps && discover_apis && generate_dynamic_tests && run_benchmark "dynamic" "Dynamic API Testing"
elif [[ $STATIC_ONLY -eq 1 ]]; then
    check_api && install_deps && run_benchmark "light" "Light Load" && run_benchmark "medium" "Medium Load"
else
    main
fi
