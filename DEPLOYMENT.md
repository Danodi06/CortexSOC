# Deployment Guide

## Local Development

### Prerequisites
- Python 3.10+
- pip or poetry

### Setup

```bash
# Clone or navigate to the repository
cd CortexSOC

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run Locally

```powershell
# Windows PowerShell
$env:PYTHONPATH = "${PWD}\src"
uvicorn src.cortexsoc.app:app --reload --port 8000
```

```bash
# Linux/macOS
export PYTHONPATH="${PWD}/src"
uvicorn src.cortexsoc.app:app --reload --port 8000
```

**Dashboard:** http://127.0.0.1:8000/static/index.html

### Run Integration Tests

```bash
python test_integration.py
```

## Production Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.13-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY config/ config/

ENV PYTHONPATH=/app/src
ENV DATABASE_URL=postgresql://user:password@db:5432/cortexsoc

EXPOSE 8000

CMD ["uvicorn", "src.cortexsoc.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Build and run:**

```bash
docker build -t cortexsoc:latest .
docker run -p 8000:8000 -e DATABASE_URL="postgresql://..." cortexsoc:latest
```

### Docker Compose

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: cortexsoc
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: cortexsoc
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      DATABASE_URL: postgresql://cortexsoc:secure_password@postgres:5432/cortexsoc
    depends_on:
      - postgres

volumes:
  postgres_data:
```

**Run:**

```bash
docker-compose up -d
```

### Cloud Deployment

#### AWS (Elastic Container Service)

```bash
# Build and push to ECR
aws ecr create-repository --repository-name cortexsoc
docker build -t cortexsoc:latest .
docker tag cortexsoc:latest <account>.dkr.ecr.us-east-1.amazonaws.com/cortexsoc:latest
aws ecr get-login-password | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
docker push <account>.dkr.ecr.us-east-1.amazonaws.com/cortexsoc:latest

# Use ECS task definition to deploy
```

#### Google Cloud (Cloud Run)

```bash
gcloud builds submit --tag gcr.io/PROJECT_ID/cortexsoc
gcloud run deploy cortexsoc --image gcr.io/PROJECT_ID/cortexsoc --platform managed
```

#### Azure (Container Instances)

```bash
az acr build --registry myregistry --image cortexsoc:latest .
az container create --resource-group mygroup --name cortexsoc --image myregistry.azurecr.io/cortexsoc:latest --port 8000
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cortexsoc-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cortexsoc
  template:
    metadata:
      labels:
        app: cortexsoc
    spec:
      containers:
      - name: cortexsoc
        image: cortexsoc:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: cortexsoc-secrets
              key: database-url
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: cortexsoc-service
spec:
  selector:
    app: cortexsoc
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

**Deploy:**

```bash
kubectl apply -f deployment.yaml
kubectl get service cortexsoc-service  # Get external IP
```

## Environment Configuration

Create a `.env` file or set environment variables:

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/cortexsoc

# API
PORT=8000

# Notifications
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Response Actions
ALLOWED_RESPONSE_ACTIONS=block_ip,disable_account,alert
```

## Database Setup

### PostgreSQL (Recommended)

```bash
# Create database
createdb cortexsoc

# Set connection string
export DATABASE_URL="postgresql://user:password@localhost:5432/cortexsoc"
```

### SQLite (Local Development)

```bash
# Auto-created on first run
export DATABASE_URL="sqlite:///./cortexsoc.db"
```

## Security Hardening

### Before Production

1. **Enable HTTPS:**
   ```bash
   # Use a reverse proxy (nginx, HAProxy)
   # or set up Let's Encrypt SSL
   ```

2. **Add API Authentication:**
   ```python
   # Implement in app.py
   from fastapi.security import APIKeyHeader
   api_key = APIKeyHeader(name="X-API-Key")
   ```

3. **Enable CORS (if needed):**
   ```python
   from fastapi.middleware.cors import CORSMiddleware
   app.add_middleware(CORSMiddleware, allow_origins=["https://yourdomain.com"])
   ```

4. **Rate Limiting:**
   ```bash
   pip install slowapi
   # Implement in app.py
   ```

5. **Audit Logging:**
   - Log all incident actions to a file or SIEM
   - Use `logging` module in production

6. **Secrets Management:**
   - Use AWS Secrets Manager, Azure Key Vault, or HashiCorp Vault
   - Never commit `.env` files with real secrets

## Monitoring & Logging

### Application Logging

```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cortexsoc.log'),
        logging.StreamHandler()
    ]
)
```

### Metrics & Observability

Integrate with monitoring tools:

```bash
# Prometheus metrics
pip install prometheus-client

# Add to app.py
from prometheus_client import Counter, Histogram
request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')
```

### Log Aggregation

- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Datadog**
- **New Relic**
- **CloudWatch** (AWS)

## Troubleshooting

### Server won't start
```bash
# Check port is available
lsof -i :8000  # Unix
netstat -ano | findstr :8000  # Windows

# Kill process if needed
kill -9 <PID>
```

### Database connection fails
```bash
# Verify DATABASE_URL format
echo $DATABASE_URL

# Test PostgreSQL connection
psql $DATABASE_URL

# Check logs for detailed error
```

### Performance issues
- Use PostgreSQL instead of SQLite for large datasets
- Add database indexes on frequently queried columns
- Implement caching with Redis
- Scale horizontally with Kubernetes

## Scaling Considerations

### Horizontal Scaling
- Deploy multiple API instances behind a load balancer
- Use a shared database (PostgreSQL) for state
- Consider message queue (Kafka) for log processing

### Vertical Scaling
- Increase CPU/memory for single instance
- Use database connection pooling
- Optimize detection algorithms

## Health Checks

The API exposes a health endpoint:

```bash
curl http://127.0.0.1:8000/health
# Response: {"status": "ok"}
```

Use this for load balancer health checks and monitoring.

## Backup & Disaster Recovery

### PostgreSQL Backups

```bash
# Full backup
pg_dump cortexsoc > backup.sql

# Restore
psql cortexsoc < backup.sql

# Automated daily backups
# Use AWS RDS automated backups or similar
```

### Data Retention

Set up log retention policies:

```python
# Auto-delete logs older than 90 days
from datetime import datetime, timedelta
cutoff = datetime.utcnow() - timedelta(days=90)
session.query(Log).filter(Log.timestamp < cutoff).delete()
```

## Support & Maintenance

- Monitor disk space for database growth
- Update dependencies regularly (`pip install -U -r requirements.txt`)
- Review and rotate API keys/secrets monthly
- Test incident response playbooks regularly
