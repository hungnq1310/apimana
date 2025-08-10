## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Git
- Docker (optional, for containerized deployment)

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd apimana
```

2. **Run the setup script**
```bash
./setup.sh
```

3. **Activate virtual environment**
```bash
source venv/bin/activate
```

4. **Start the gateway**
```bash
python main.py
```

5. **Visit the API documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Using Makefile

The project includes a Makefile for common tasks:

```bash
# Install and setup
make install

# Run in development
make dev

# Run tests
make test

# Run with Docker
make docker-run

# View logs
make logs

# Clean up
make clean
```

### Configuration

1. **Edit `.env` file** with your specific settings
2. **Modify `gateway_config.yaml`** for service configurations  
3. **Update router configurations** in `configs/router_loader.py`

### Adding Real Services

Replace the placeholder services with actual git submodules:

```bash
# Remove placeholder services
rm -rf external/user-service
rm -rf external/product-service
rm -rf external/order-service

# Add real services as submodules
git submodule add [USER_REPO_URL] external/user-service
git submodule add [PRODUCT_REPO_URL] external/product-service
git submodule add [ORDER_REPO_URL] external/order-service

# Update submodules
git submodule update --init --recursive
```

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f gateway

# Stop services
docker-compose down
```

## 📁 Project Structure

```
apimana/
├── main.py                    # Main application entry point
├── requirements.txt           # Python dependencies
├── gateway_config.yaml        # Gateway configuration
├── .env.example              # Environment variables template
├── setup.sh                  # Project setup script
├── Makefile                  # Development workflow commands
├── Dockerfile                # Docker container definition
├── docker-compose.yml        # Docker services orchestration
├── init-db.sql              # Database initialization
├── configs/
│   ├── __init__.py
│   ├── router_loader.py      # Dynamic router loading system
│   └── config_manager.py     # Configuration management
├── external/
│   ├── user-service/         # User service (placeholder/submodule)
│   ├── product-service/      # Product service (placeholder/submodule)
│   └── order-service/        # Order service (placeholder/submodule)
├── tests/
│   ├── __init__.py
│   ├── test_router_loader.py # Router loader tests
│   └── test_config_manager.py # Config manager tests
└── docs/
    └── API_DOCS.md           # Comprehensive API documentation
```

## 🔧 Development

### Running Tests

```bash
# Run all tests
make test

# Run tests with coverage
make test-cov

# Run specific test file
pytest tests/test_router_loader.py -v
```

### Code Quality

```bash
# Format code
make format

# Run linting
make lint

# Security check
make security-check
```

### Database Management

```bash
# Initialize database
make db-init

# Reset database
make db-reset

# Create backup
make db-backup
```

## 📊 Monitoring

- **Health Check**: `GET /health`
- **Gateway Status**: `GET /gateway/status`
- **Services List**: `GET /gateway/services`

## 🐛 Troubleshooting

1. **Import errors**: Make sure all dependencies are installed: `pip install -r requirements.txt`
2. **Service not loading**: Check the module path and router name in `ROUTER_CONFIGS`
3. **Configuration issues**: Verify YAML syntax and environment variables
4. **Port conflicts**: Change the port in `gateway_config.yaml` or `.env`

For detailed troubleshooting, see [docs/API_DOCS.md](docs/API_DOCS.md).

**Implementation completed!** ✅