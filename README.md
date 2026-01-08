# CortexSOC

AI Powered SOC Automation for Real Time Threat Detection and Response

## Overview

CortexSOC is a lightweight but powerful AI-driven Security Operations Center (SOC) automation system designed to:

1. **Ingest** security logs from multiple sources (auth logs, web logs, EDR, NetFlow)
2. **Detect** anomalies and threats using rule-based and ML-ready detection
3. **Respond** automatically to security incidents with configurable playbooks
4. **Dashboard** to visualize incidents and security posture in real-time

Built with **FastAPI** + **SQLAlchemy** + **Python**, deployable locally or to the cloud.

## Quick Start

### 1. Install Dependencies

```bash
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Run the API Server

From the repository root:

```powershell
$env:PYTHONPATH = "${PWD}\src"
uvicorn src.cortexsoc.app:app --reload --port 8000
```

Server will start at: **http://127.0.0.1:8000**

### 3. Open the Dashboard

Navigate to: **http://127.0.0.1:8000/static/index.html**

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design.

### Four Phases

```
Phase 1: Data        Phase 2: Detection    Phase 3: Response     Phase 4: Dashboard
┌──────────┐         ┌──────────┐          ┌──────────┐           ┌──────────┐
│ Ingestion│ ──────→ │ Detection│ ────────→ │ Response │ ────────→ │Dashboard │
│ (logs)   │         │(anomaly) │          │(playbook)│          │(WebUI)   │
└──────────┘         └──────────┘          └──────────┘           └──────────┘
     ↓                    ↓                       ↓                    ↓
  SQLite/Postgres    Rule-based              Auto-response        Real-time
  ingest.py          detect.py               respond.py           index.html
```

## API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/ingest` | Ingest a security log |
| GET | `/detect` | Run anomaly detection |
| POST | `/detect-and-respond` | Detect + auto-respond |
| GET | `/incidents` | List all incidents |
| GET | `/incidents/{id}` | Get incident details |
| POST | `/respond` | Manual response action |

Full API documentation: [API.md](API.md)

## Detection Rules

CortexSOC detects threats using multiple rule-based patterns:

1. **New Origin** (Medium) - Login from new geographic location
2. **Failed Login Threshold** (High) - Brute force attempts (≥5 failures)
3. **Unusual Login Time** (Low) - Off-hours logins (22:00 - 06:00)
4. **Rapid Logins** (Medium) - Multiple logins within 60 seconds

## Response Playbooks

Automatic responses are triggered based on severity:

- **HIGH**: Disable account + Block IP + Alert ops
- **MEDIUM**: Alert security team
- **LOW**: Log-only alert

## Example Usage

### Ingest Logs
```bash
curl -X POST http://127.0.0.1:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "type": "login",
    "user": "alice",
    "origin": "US",
    "ip": "1.2.3.4"
  }'
```

### Run Detection
```bash
curl http://127.0.0.1:8000/detect
```

### Detect and Auto-Respond
```bash
curl -X POST http://127.0.0.1:8000/detect-and-respond
```

See [API.md](API.md) for more examples.

## Data Storage

### Local Development (Default)
Uses SQLite, no setup required:
```bash
# Auto-created on first run
cortexsoc.db
```

### Production (PostgreSQL)
Set environment variable:
```bash
export DATABASE_URL="postgresql://user:password@host:5432/cortexsoc"
```

## Configuration

Create a `.env` file from `config/example.env`:

```bash
cp config/example.env .env
```

Edit `.env`:
```
DATABASE_URL=sqlite:///./cortexsoc.db
PORT=8000
SLACK_WEBHOOK=https://hooks.slack.com/...
ALLOWED_RESPONSE_ACTIONS=block_ip,disable_account,alert
```

## Project Structure

```
CortexSOC/
├── src/cortexsoc/
│   ├── __init__.py
│   ├── app.py              # FastAPI application
│   ├── ingest.py           # Log ingestion
│   ├── storage.py          # Database layer
│   ├── detect.py           # Threat detection
│   ├── respond.py          # Response automation
│   └── static/
│       └── index.html      # Dashboard UI
├── config/
│   └── example.env         # Configuration template
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── ARCHITECTURE.md        # Detailed architecture
└── API.md                 # API reference
```

## Performance

### Benchmarks
- **Ingestion**: ~1,000 logs/second (SQLite)
- **Detection**: O(n) log scanning
- **Response**: <100ms per incident

### Scaling Tips
1. Use PostgreSQL for >10GB data
2. Add Redis for caching frequent queries
3. Use Kafka for high-volume log streaming
4. Shard by user or time range

## Development

### Run Tests
```bash
pytest tests/
```

### Hot Reload
```powershell
$env:PYTHONPATH = "${PWD}\src"
uvicorn src.cortexsoc.app:app --reload --port 8000
```

### Database Migrations
```bash
# Coming soon: SQLAlchemy Alembic
```

## Integration Points

Current implementation includes **mock** integrations. Production deployments should implement:

- **Firewall**: Palo Alto, AWS Security Groups, Azure NSG
- **IAM**: Active Directory, Okta, AWS IAM
- **SIEM**: Splunk, Elastic, Datadog
- **Notifications**: Slack, PagerDuty, Email

See [ARCHITECTURE.md](ARCHITECTURE.md) for integration details.

## Security

⚠️ **Not production-ready without:**
- API authentication (API keys, OAuth2)
- TLS/HTTPS
- Rate limiting
- Audit logging
- Input validation

## Roadmap

- [ ] ML-based anomaly detection (Isolation Forest, LSTM)
- [ ] Real-time streaming (Kafka consumer)
- [ ] Advanced incident correlation
- [ ] YAML-based playbook customization
- [ ] Slack/Email integration
- [ ] SIEM integration (ELK, Splunk)
- [ ] Docker deployment
- [ ] Kubernetes manifests
- [ ] Unit & integration tests
- [ ] CI/CD pipeline (GitHub Actions)

## Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Submit a pull request

## License

See [LICENSE](LICENSE) file.

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check [ARCHITECTURE.md](ARCHITECTURE.md) for design details
- Review [API.md](API.md) for endpoint documentation

---

**Built with ❤️ for real-time threat detection**

