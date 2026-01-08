# CortexSOC Architecture

## Overview

CortexSOC is an AI-driven SOC (Security Operations Center) automation system designed for real-time threat detection and response. The system is built as a modular Python FastAPI application with four core components:

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CortexSOC System                             │
└─────────────────────────────────────────────────────────────────┘
         │
         ├─ [Phase 1: Data Ingestion]
         │  ├─ ingest.py: Log collection endpoint
         │  ├─ storage.py: SQLAlchemy ORM (SQLite/PostgreSQL)
         │  └─ HTTP POST /ingest
         │
         ├─ [Phase 2: Detection]
         │  ├─ detect.py: Rule-based anomaly detection
         │  ├─ Rules:
         │  │  - New login origins
         │  │  - Failed login thresholds (brute force)
         │  │  - Unusual login times (off-hours)
         │  │  - Rapid multiple logins
         │  └─ HTTP GET /detect
         │
         ├─ [Phase 3: Response]
         │  ├─ respond.py: Auto-response playbooks
         │  ├─ Actions:
         │  │  - Block IP (firewall integration)
         │  │  - Disable account (IAM integration)
         │  │  - Send alerts (Slack/Email)
         │  └─ HTTP POST /detect-and-respond
         │
         └─ [Phase 4: Dashboard]
            ├─ static/index.html: Real-time web UI
            └─ HTTP GET /static/index.html
```

## Module Structure

### 1. **ingest.py** - Log Ingestion
- Accepts log records from various sources (auth logs, web logs, EDR, NetFlow)
- Writes to persistent storage (DB) with in-memory fallback
- Supports custom log formats via JSON

**Key Functions:**
- `ingest_log(record)` - Persist a log record
- `get_logs(limit=100)` - Retrieve recent logs

### 2. **storage.py** - Data Persistence
- SQLAlchemy ORM with support for SQLite and PostgreSQL
- Log table with fields: id, timestamp, type, user, ip, origin, raw
- Thread-safe database initialization and queries

**Key Functions:**
- `init_db(database_url)` - Initialize DB connection
- `write_log(record)` - Persist log to DB
- `get_logs(limit)` - Query logs from DB

### 3. **detect.py** - Threat Detection
Implements multiple detection rules with severity levels:

**Rules:**
1. **new_origin** (medium) - User login from new geographic origin
2. **failed_login_threshold** (high) - Excessive failed login attempts (≥5)
3. **unusual_login_time** (low) - Login outside business hours (22:00 - 06:00)
4. **rapid_logins** (medium) - Multiple logins within 60 seconds

Each alert includes severity, reason, user, IP, and metadata for routing.

### 4. **respond.py** - Automated Response
- Incident tracking with full action history
- Severity-based playbooks for automated response

**Playbooks:**
- **HIGH** severity: Disable account + Block IP + Alert ops
- **MEDIUM** severity: Alert security team
- **LOW** severity: Log-only alert

**Key Functions:**
- `create_incident(alert)` - Create incident from alert
- `auto_respond_to_alert(alert)` - Execute response playbook
- `get_incidents()` - Return all incidents

### 5. **app.py** - FastAPI Server
Exposes REST endpoints and serves the dashboard.

**Endpoints:**
- `GET /health` - Server health check
- `POST /ingest` - Ingest a log record
- `GET /detect` - Run detection on all logs
- `POST /detect-and-respond` - Detect and auto-respond
- `GET /incidents` - List all incidents
- `GET /incidents/{id}` - Get specific incident details

## Data Flow

```
[Data Sources]
    ↓
[POST /ingest] → [ingest.py] → [storage.py] → [Database]
    ↓
[GET /detect] → [detect.py] (reads from storage) → [Alerts]
    ↓
[POST /detect-and-respond] → [respond.py] (executes playbooks) → [Incidents]
    ↓
[Dashboard] ← [API Responses] ← [app.py]
```

## Deployment Options

### Local Development
```bash
# SQLite (default)
DATABASE_URL=sqlite:///./cortexsoc.db
uvicorn src.cortexsoc.app:app --reload --port 8000
```

### Production (PostgreSQL)
```bash
# PostgreSQL on AWS RDS, Azure Database, or self-hosted
DATABASE_URL=postgresql://user:pass@host:5432/cortexsoc
uvicorn src.cortexsoc.app:app --port 8000 --workers 4
```

### Docker (Coming Soon)
```dockerfile
FROM python:3.13-slim
RUN pip install -r requirements.txt
EXPOSE 8000
CMD ["uvicorn", "src.cortexsoc.app:app", "--host", "0.0.0.0"]
```

## Integration Points (Stubbed)

Current implementation uses mock integrations. Production deployments should implement:

1. **Firewall Integration** - `respond.py:block_ip()`
   - Palo Alto Networks
   - AWS Security Groups
   - Azure NSG

2. **IAM Integration** - `respond.py:disable_account()`
   - Active Directory / Okta
   - AWS IAM
   - Azure AD

3. **Notification** - `respond.py:send_alert()`
   - Slack SDK
   - PagerDuty
   - Email (SMTP)

## Extensibility

### Adding New Detection Rules
```python
# In detect.py
def rule_custom_anomaly(logs):
    alerts = []
    for r in logs:
        if detect_custom_condition(r):
            alerts.append({
                "reason": "custom_anomaly",
                "severity": "medium",
                "record": r
            })
    return alerts

# Register in detect_all()
def detect_all(logs):
    results = []
    results.extend(rule_custom_anomaly(logs))
    return results
```

### Adding New Response Actions
```python
# In respond.py
def custom_action(target, incident):
    logger.info(f"Custom action on {target}")
    # Implement integration
    incident.add_action("custom_action", target, "success", "details")
    return {"status": "success"}

# Use in auto_respond_to_alert()
if reason == "custom_anomaly":
    custom_action(user, incident)
```

## Performance & Scaling

### Current Benchmarks
- Ingestion: ~1000 logs/second (in-memory)
- Detection: O(n) time for log scanning
- DB queries: SQLite suitable for <10GB; PostgreSQL for larger deployments

### Scaling Strategies
1. **Sharding** - Split logs by user or time range
2. **Caching** - Redis for frequent queries
3. **Message Queue** - Kafka/RabbitMQ for async processing
4. **Time-series DB** - InfluxDB/TimescaleDB for analytics

## Security Considerations

1. **Authentication** - Add API keys / OAuth for endpoints
2. **TLS** - Enable HTTPS in production
3. **Rate Limiting** - Prevent abuse of /detect-and-respond
4. **Audit Logging** - Log all incident actions for compliance
5. **Encryption** - Encrypt sensitive fields (passwords, keys)

## Future Enhancements

1. **ML-based Anomaly Detection**
   - Isolation Forest for unsupervised learning
   - LSTM for time-series analysis
   - Model training pipeline

2. **Real-time Streaming**
   - Kafka consumer for live event processing
   - WebSocket updates to dashboard

3. **Advanced Incident Management**
   - Correlation of related alerts
   - Incident severity scoring
   - Escalation workflows

4. **Compliance & Reporting**
   - SIEM integration (Splunk, ELK)
   - Audit trails for SOC2/ISO27001
   - Automated reporting

5. **Advanced Response**
   - Playbook customization via YAML
   - Custom webhook actions
   - Integration with SOAR platforms
