# Docker Development and Deployment Strategy

## Overview
This document outlines a Kubernetes-ready Docker strategy for the Coinolio API, with separate configurations for local development and production deployment.

## Container Strategy

### Directory Structure
```
docker/
├── local/
│   └── docker-compose.yml    # Full stack for local development
└── Dockerfile               # Single Dockerfile for both environments
```

### Environment Configuration

Create a `.env` file in the project root:

```env
# API Configuration
API_PORT=3000

# Database Configuration
POSTGRES_HOST=db
POSTGRES_USER=coinolio
POSTGRES_PASSWORD=development
POSTGRES_DB=coinolio

# Redis Configuration
REDIS_URL=redis://cache:6379/0

# Environment
ENVIRONMENT=development
```

### Local Development Configuration

#### docker-compose.yml
```yaml
version: '3.8'

services:
  app:
    build:
      context: ../..
      dockerfile: docker/Dockerfile
    ports:
      - "${API_PORT}:${API_PORT}"
    environment:
      - ENVIRONMENT=${ENVIRONMENT}
      - API_PORT=${API_PORT}
      - POSTGRES_HOST=${POSTGRES_HOST}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
      - REDIS_URL=${REDIS_URL}
    volumes:
      - ../..:/app
    depends_on:
      - db
      - cache
    command: uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT} --reload

  db:
    image: postgres:15-alpine
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=${POSTGRES_DB}
    ports:
      - "5432:5432"

  cache:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Production Configuration

The production environment uses a single container for the API, expecting external database connections:

```yaml
# Example Kubernetes deployment snippet
apiVersion: apps/v1
kind: Deployment
metadata:
  name: coinolio-api
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: api
        image: ${REGISTRY}/coinolio-api:${TAG}
        ports:
        - containerPort: ${API_PORT}
        env:
        - name: API_PORT
          valueFrom:
            configMapKeyRef:
              name: api-config
              key: port
        - name: ENVIRONMENT
          value: "production"
        - name: POSTGRES_HOST
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: host
        - name: POSTGRES_USER
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: username
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: password
        - name: POSTGRES_DB
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: database
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-credentials
              key: url
```

### Dockerfile
```dockerfile
# Build stage
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Final stage
FROM python:3.12-slim

WORKDIR /app

# Copy only necessary files from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=builder /usr/lib/x86_64-linux-gnu/libpq.so* /usr/lib/x86_64-linux-gnu/

# Create non-root user
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

# Copy application code
COPY . .

# Default command (can be overridden in docker-compose for development)
CMD uvicorn app.main:app --host 0.0.0.0 --port ${API_PORT}
```

## Development Workflow

1. **Environment Setup**
   ```bash
   # Copy example environment file
   cp .env.example .env

   # Edit .env file with your desired configuration
   # Default values are provided in .env.example
   ```

2. **Local Development**
   ```bash
   # Start local development environment with hot reload
   cd docker/local
   docker-compose up -d

   # Run tests in the local environment
   docker-compose exec app pytest

   # Run migrations
   docker-compose exec app alembic upgrade head

   # View logs
   docker-compose logs -f app
   ```

3. **Development Features**
   - Full stack environment with PostgreSQL and Redis
   - Hot reload for rapid development
   - Mounted volumes for local code changes
   - Easy access to logs and debugging
   - Configurable through .env file

## Production Workflow

1. **Building Production Image**
   ```bash
   # Build the production image
   docker build -t coinolio-api:latest -f docker/Dockerfile .

   # Push to container registry
   docker tag coinolio-api:latest ${REGISTRY}/coinolio-api:${TAG}
   docker push ${REGISTRY}/coinolio-api:${TAG}
   ```

2. **Production Features**
   - Minimal container with only the API
   - Configurable through environment variables
   - Expects external database connections
   - Ready for Kubernetes deployment

## Container Design Principles

1. **Environment Separation**
   - Local: Full stack for development and testing
   - Production: API only, external dependencies

2. **Configuration Management**
   - Environment variables for all configurable values
   - Local development uses .env file
   - Production uses Kubernetes ConfigMaps and Secrets

3. **Kubernetes Readiness**
   - Stateless application container
   - Environment variable configuration
   - Health check endpoint support
   - Suitable for horizontal scaling

4. **Security**
   - Multi-stage builds for smaller attack surface
   - Non-root user
   - Minimal base images
   - Secrets management through Kubernetes

## Infrastructure Considerations

1. **External Services (Production)**
   - Managed PostgreSQL database
   - Managed Redis instance
   - Ingress controller for routing
   - SSL/TLS termination at ingress

2. **DevOps Integration**
   - CI/CD pipeline for testing and deployment
   - Kubernetes manifests in separate repository
   - Infrastructure as Code for cloud resources

## Next Steps

1. **Implementation Priority**
   - Create .env.example file
   - Set up local development environment
   - Test end-to-end functionality locally
   - Create production Kubernetes manifests
   - Configure CI/CD pipeline

2. **Future Considerations**
   - Add database migration jobs
   - Set up monitoring and logging
   - Configure autoscaling
   - Implement GitOps workflow
