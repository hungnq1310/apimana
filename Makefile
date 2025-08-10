# Makefile for API Gateway project

.PHONY: help install dev test clean build run docker-build docker-run docker-stop logs

# Default target
help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies and setup project"
	@echo "  dev         - Run in development mode"
	@echo "  test        - Run tests"
	@echo "  test-cov    - Run tests with coverage"
	@echo "  clean       - Clean up temporary files"
	@echo "  build       - Build Docker image"
	@echo "  run         - Run the application"
	@echo "  docker-build - Build Docker image"
	@echo "  docker-run   - Run with Docker Compose"
	@echo "  docker-stop  - Stop Docker Compose services"
	@echo "  logs        - Show Docker Compose logs"
	@echo "  lint        - Run code linting"
	@echo "  format      - Format code"

# Install dependencies and setup project
install:
	@echo "Setting up the project..."
	@./setup.sh

# Run in development mode
dev:
	@echo "Starting development server..."
	@source venv/bin/activate && python main.py

# Run tests
test:
	@echo "Running tests..."
	@source venv/bin/activate && pytest tests/ -v

# Run tests with coverage
test-cov:
	@echo "Running tests with coverage..."
	@source venv/bin/activate && pytest tests/ -v --cov=configs --cov=main --cov-report=html --cov-report=term

# Clean up temporary files
clean:
	@echo "Cleaning up..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache htmlcov .coverage 2>/dev/null || true
	@echo "Cleanup completed"

# Build application (placeholder for build steps)
build:
	@echo "Building application..."
	@source venv/bin/activate && python -c "from main import create_app; print('Build check passed')"

# Run the application
run:
	@echo "Running application..."
	@source venv/bin/activate && python main.py

# Docker commands
docker-build:
	@echo "Building Docker image..."
	@docker build -t api-gateway:latest .

docker-run:
	@echo "Starting services with Docker Compose..."
	@docker-compose up -d

docker-stop:
	@echo "Stopping Docker Compose services..."
	@docker-compose down

docker-logs:
	@echo "Showing Docker Compose logs..."
	@docker-compose logs -f

# Show logs
logs:
	@docker-compose logs -f gateway

# Linting
lint:
	@echo "Running linting..."
	@source venv/bin/activate && flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
	@source venv/bin/activate && flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

# Format code
format:
	@echo "Formatting code..."
	@source venv/bin/activate && black . --line-length=88
	@source venv/bin/activate && isort .

# Setup git hooks
setup-hooks:
	@echo "Setting up git hooks..."
	@echo "#!/bin/sh\nmake lint && make test" > .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "Git hooks setup completed"

# Development setup with all tools
dev-setup: install setup-hooks
	@echo "Development environment setup completed"

# Full test suite
test-all: lint test
	@echo "All tests completed"

# Deploy to staging
deploy-staging:
	@echo "Deploying to staging..."
	@docker-compose -f docker-compose.staging.yml up -d

# Deploy to production  
deploy-prod:
	@echo "Deploying to production..."
	@docker-compose -f docker-compose.prod.yml up -d

# Database commands
db-init:
	@echo "Initializing database..."
	@docker-compose exec postgres psql -U postgres -f /docker-entrypoint-initdb.d/init-db.sql

db-reset:
	@echo "Resetting database..."
	@docker-compose down -v
	@docker-compose up -d postgres
	@sleep 5
	@make db-init

# Backup database
db-backup:
	@echo "Creating database backup..."
	@docker-compose exec postgres pg_dumpall -U postgres > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Monitor services
monitor:
	@echo "Monitoring services..."
	@docker-compose exec gateway python -c "
import requests
import time
while True:
    try:
        r = requests.get('http://localhost:8000/health')
        print(f'Gateway: {r.status_code} - {r.json()}')
    except:
        print('Gateway: Not responding')
    time.sleep(30)
"

# Generate requirements.txt from current environment
freeze:
	@echo "Generating requirements.txt..."
	@source venv/bin/activate && pip freeze > requirements.txt

# Check for security vulnerabilities
security-check:
	@echo "Checking for security vulnerabilities..."
	@source venv/bin/activate && safety check

# Update dependencies
update-deps:
	@echo "Updating dependencies..."
	@source venv/bin/activate && pip list --outdated
	@source venv/bin/activate && pip install --upgrade pip
	@echo "Review outdated packages and update requirements.txt as needed"
