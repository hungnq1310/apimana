#!/bin/bash

# API Gateway Performance Testing Script
# This script provides easy commands to run different types of performance tests

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default configuration
DEFAULT_HOST="http://localhost:8000"
LOCUST_FILE="benchmark/locustfile.py"
RESULTS_DIR="benchmark/results"

# Create results directory if it doesn't exist
mkdir -p "$RESULTS_DIR"

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if locust is installed
check_locust() {
    if ! command -v locust &> /dev/null; then
        print_error "Locust is not installed. Please install it with: pip install locust"
        exit 1
    fi
}

# Function to check if the API is running
check_api() {
    local host=${1:-$DEFAULT_HOST}
    print_info "Checking if API is running at $host..."
    
    if curl -s "$host/health" > /dev/null; then
        print_success "API is running and healthy"
    else
        print_warning "API might not be running or not healthy at $host"
        print_info "Make sure to start your API server first"
    fi
}

# Function to run a benchmark test
run_benchmark() {
    local test_type=$1
    local host=${2:-$DEFAULT_HOST}
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local results_file="$RESULTS_DIR/benchmark_${test_type}_${timestamp}"
    
    print_info "Starting $test_type benchmark test..."
    print_info "Target host: $host"
    print_info "Results will be saved to: $results_file"
    
    case $test_type in
        "light")
            locust -f "$LOCUST_FILE" --host="$host" --users=5 --spawn-rate=1 --run-time=60s --html="$results_file.html" --csv="$results_file" --headless
            ;;
        "medium")
            locust -f "$LOCUST_FILE" --host="$host" --users=20 --spawn-rate=5 --run-time=120s --html="$results_file.html" --csv="$results_file" --headless
            ;;
        "heavy")
            locust -f "$LOCUST_FILE" --host="$host" --users=50 --spawn-rate=10 --run-time=300s --html="$results_file.html" --csv="$results_file" --headless
            ;;
        "stress")
            locust -f "$LOCUST_FILE" --host="$host" --users=100 --spawn-rate=20 --run-time=600s --html="$results_file.html" --csv="$results_file" --headless
            ;;
        "spike")
            locust -f "$LOCUST_FILE" --host="$host" --users=200 --spawn-rate=50 --run-time=180s --html="$results_file.html" --csv="$results_file" --headless
            ;;
        "interactive")
            print_info "Starting interactive mode..."
            locust -f "$LOCUST_FILE" --host="$host"
            ;;
        *)
            print_error "Unknown test type: $test_type"
            print_info "Available test types: light, medium, heavy, stress, spike, interactive"
            exit 1
            ;;
    esac
    
    if [ "$test_type" != "interactive" ]; then
        print_success "Benchmark completed! Results saved to $results_file.html"
    fi
}

# Function to run quick health check
run_health_check() {
    local host=${1:-$DEFAULT_HOST}
    
    print_info "Running quick health check..."
    locust -f "$LOCUST_FILE" --host="$host" --users=1 --spawn-rate=1 --run-time=10s --headless
}

# Function to show usage
show_usage() {
    echo "API Gateway Performance Testing Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  light      - Light load test (5 users, 60s)"
    echo "  medium     - Medium load test (20 users, 120s)"
    echo "  heavy      - Heavy load test (50 users, 300s)"
    echo "  stress     - Stress test (100 users, 600s)"
    echo "  spike      - Spike test (200 users, 180s)"
    echo "  interactive- Interactive mode with web UI"
    echo "  health     - Quick health check"
    echo "  check      - Check if API is running"
    echo "  install    - Install locust dependencies"
    echo "  help       - Show this help message"
    echo ""
    echo "Options:"
    echo "  --host URL - Target host (default: http://localhost:8000)"
    echo ""
    echo "Examples:"
    echo "  $0 light                                    # Run light test on default host"
    echo "  $0 medium --host http://localhost:8080     # Run medium test on custom host"
    echo "  $0 interactive                             # Start interactive mode"
    echo "  $0 check --host http://localhost:8000      # Check if API is running"
}

# Function to install dependencies
install_dependencies() {
    print_info "Installing Locust and dependencies..."
    pip install locust requests
    print_success "Dependencies installed successfully!"
}

# Main script logic
main() {
    local command=$1
    local host=$DEFAULT_HOST
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --host)
                host="$2"
                shift 2
                ;;
            --help|-h)
                show_usage
                exit 0
                ;;
            *)
                if [ -z "$command" ]; then
                    command="$1"
                fi
                shift
                ;;
        esac
    done
    
    # Handle commands
    case $command in
        "install")
            install_dependencies
            ;;
        "check")
            check_api "$host"
            ;;
        "health")
            check_locust
            check_api "$host"
            run_health_check "$host"
            ;;
        "light"|"medium"|"heavy"|"stress"|"spike"|"interactive")
            check_locust
            check_api "$host"
            run_benchmark "$command" "$host"
            ;;
        "help"|"")
            show_usage
            ;;
        *)
            print_error "Unknown command: $command"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"
