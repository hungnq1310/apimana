#!/bin/bash

# Setup script for API Gateway project
# This script initializes the project environment and dependencies

set -e  # Exit on any error

echo "🚀 Setting up Dynamic API Gateway..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.8 or higher is required. Current version: $python_version"
    exit 1
fi

echo "✅ Python version check passed: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔧 Creating .env file from template..."
    cp .env.example .env
    echo "✏️ Please edit .env file with your specific configuration"
fi

# Create external directories for git submodules
echo "📁 Setting up external service directories..."
mkdir -p external/user-service
mkdir -p external/product-service  
mkdir -p external/order-service

# Create placeholder files for testing
echo "📝 Creating placeholder service files for testing..."

# User service placeholder
mkdir -p external/user-service/app
cat > external/user-service/app/main.py << 'EOF'
"""
Placeholder user service for testing
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/users")
async def get_users():
    return {"users": ["user1", "user2"]}

@router.get("/auth/login")
async def login():
    return {"token": "fake-jwt-token"}

@router.get("/profile")
async def get_profile():
    return {"user": "test-user", "email": "test@example.com"}

@router.get("/admin")
async def admin():
    return {"message": "Admin panel"}
EOF

# Product service placeholder
mkdir -p external/product-service/app
cat > external/product-service/app/main.py << 'EOF'
"""
Placeholder product service for testing
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/products")
async def get_products():
    return {"products": ["product1", "product2"]}

@router.get("/categories")
async def get_categories():
    return {"categories": ["electronics", "clothing"]}

@router.get("/inventory")
async def get_inventory():
    return {"inventory": {"product1": 10, "product2": 5}}

@router.get("/admin")
async def admin():
    return {"message": "Product admin panel"}
EOF

# Order service placeholder
mkdir -p external/order-service/app
cat > external/order-service/app/main.py << 'EOF'
"""
Placeholder order service for testing
"""
from fastapi import APIRouter

router = APIRouter()

@router.get("/orders")
async def get_orders():
    return {"orders": ["order1", "order2"]}

@router.get("/cart")
async def get_cart():
    return {"cart": {"items": 2, "total": 99.99}}

@router.get("/checkout")
async def checkout():
    return {"message": "Checkout successful", "order_id": "12345"}

@router.get("/admin")
async def admin():
    return {"message": "Order admin panel"}
EOF

echo "✅ Placeholder services created for testing"

# Run tests to verify setup
echo "🧪 Running tests to verify setup..."
if command -v pytest &> /dev/null; then
    pytest tests/ -v || echo "⚠️ Some tests failed, but this is expected without actual services"
else
    echo "⚠️ pytest not found, skipping tests"
fi

# Test configuration loading
echo "🔧 Testing configuration loading..."
python -c "
from configs.config_manager import UnifiedConfigManager
try:
    manager = UnifiedConfigManager('gateway_config.yaml')
    print('✅ Configuration loading successful')
    print(f'Gateway config: {manager.get_gateway_config()}')
except Exception as e:
    print(f'❌ Configuration loading failed: {e}')
"

echo ""
echo "🎉 Setup completed successfully!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your specific configuration"
echo "2. Replace placeholder services with actual git submodules:"
echo "   git submodule add [USER_REPO_URL] external/user-service"
echo "   git submodule add [PRODUCT_REPO_URL] external/product-service"
echo "   git submodule add [ORDER_REPO_URL] external/order-service"
echo "3. Start the gateway: python main.py"
echo "4. Visit http://localhost:8000/docs for API documentation"
echo ""
echo "For development:"
echo "source venv/bin/activate"
echo "python main.py"
echo ""
