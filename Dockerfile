# Multi-stage Dockerfile for API Gateway

# Build stage
FROM python:3.9-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.9-slim

# Create non-root user
RUN groupadd -r gateway && useradd -r -g gateway gateway

WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /root/.local /home/gateway/.local

# Copy application code
COPY . .

# Create directories and set permissions
RUN mkdir -p external logs && \
    chown -R gateway:gateway /app

# Switch to non-root user
USER gateway

# Add local bin to PATH
ENV PATH=/home/gateway/.local/bin:$PATH

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "main.py"]
