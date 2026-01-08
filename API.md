# CortexSOC API Reference

## Base URL
```
http://127.0.0.1:8000
```

## Endpoints

### Health Check
**GET** `/health`

Check if the API is running.

**Response:**
```json
{
  "status": "ok"
}
```

---

### Ingest Log
**POST** `/ingest`

Submit a security log for ingestion and storage.

**Request Body:**
```json
{
  "type": "login",
  "user": "alice",
  "origin": "US",
  "ip": "1.2.3.4",
  "raw": {}
}
```

**Parameters:**
- `type` (string, required): Log type (e.g., "login", "failed_login", "web_request")
- `user` (string): Username
- `origin` (string): Geographic origin (country code or location)
- `ip` (string): IP address
- `raw` (object): Additional raw log data

**Response:**
```json
{
  "ingested": {
    "id": 1,
    "timestamp": "2026-01-08T12:07:58.267523Z",
    "type": "login",
    "user": "alice",
    "ip": "1.2.3.4",
    "origin": "US",
    "raw": {}
  }
}
```

---

### Run Detection
**GET** `/detect`

Analyze ingested logs for anomalies and threats.

**Response:**
```json
[
  {
    "user": "bob",
    "reason": "failed_login_threshold",
    "severity": "high",
    "failed_count": 6,
    "record": {}
  },
  {
    "user": "alice",
    "origin": "UK",
    "reason": "new_origin",
    "severity": "medium",
    "record": {}
  }
]
```

**Alert Types:**
- `new_origin` (medium) - Login from new geographic location
- `failed_login_threshold` (high) - Too many failed attempts (≥5)
- `unusual_login_time` (low) - Login outside business hours (22:00-06:00)
- `rapid_logins` (medium) - Multiple logins within 60 seconds

---

### Detect and Respond
**POST** `/detect-and-respond`

Run detection and automatically execute response playbooks.

**Response:**
```json
{
  "alerts_generated": 8,
  "incidents_created": 8,
  "incidents": [
    {
      "id": 1,
      "alert_id": "unknown",
      "alert_reason": "failed_login_threshold",
      "user": "bob",
      "ip": null,
      "created_at": "2026-01-08T12:10:33.333888Z",
      "status": "active",
      "actions": [
        {
          "action": "disable_account",
          "target": "bob",
          "status": "success",
          "timestamp": "2026-01-08T12:10:33.333943Z",
          "details": "User bob account disabled (mock action)"
        },
        {
          "action": "alert",
          "target": "ops",
          "status": "success",
          "timestamp": "2026-01-08T12:10:33.333958Z",
          "details": "Alert sent to ops: High: Disabled account bob due to failed login threshold"
        }
      ]
    }
  ]
}
```

**Response Playbooks:**
- **HIGH severity**: Disable account + Block IP + Alert ops
- **MEDIUM severity**: Alert security team
- **LOW severity**: Log-only alert

---

### Manual Response Action
**POST** `/respond`

Execute a manual response action.

**Request Body:**
```json
{
  "action": "block_ip",
  "target": "1.2.3.4"
}
```

**Parameters:**
- `action` (string): Action type ("block_ip", "disable_account", "alert")
- `target` (string): Target (IP or username)

**Response:**
```json
{
  "action": "block_ip",
  "ip": "1.2.3.4",
  "status": "success",
  "details": "IP 1.2.3.4 added to blocklist (mock action)"
}
```

---

### Get All Incidents
**GET** `/incidents`

Retrieve all security incidents created by the system.

**Response:**
```json
[
  {
    "id": 1,
    "alert_id": "unknown",
    "alert_reason": "failed_login_threshold",
    "user": "bob",
    "ip": null,
    "created_at": "2026-01-08T12:10:33.333888Z",
    "status": "active",
    "actions": []
  }
]
```

---

### Get Incident Details
**GET** `/incidents/{incident_id}`

Retrieve details of a specific incident.

**Parameters:**
- `incident_id` (integer, path): Incident ID

**Response:**
```json
{
  "id": 1,
  "alert_id": "unknown",
  "alert_reason": "failed_login_threshold",
  "user": "bob",
  "ip": null,
  "created_at": "2026-01-08T12:10:33.333888Z",
  "status": "active",
  "actions": [
    {
      "action": "disable_account",
      "target": "bob",
      "status": "success",
      "timestamp": "2026-01-08T12:10:33.333943Z",
      "details": "User bob account disabled (mock action)"
    }
  ]
}
```

---

## cURL Examples

### Ingest a Login
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

### Get Incidents
```bash
curl http://127.0.0.1:8000/incidents
```

### Get Specific Incident
```bash
curl http://127.0.0.1:8000/incidents/1
```

### Block an IP
```bash
curl -X POST http://127.0.0.1:8000/respond \
  -H "Content-Type: application/json" \
  -d '{
    "action": "block_ip",
    "target": "1.2.3.4"
  }'
```

---

## Error Responses

### 400 Bad Request
```json
{
  "detail": "unknown action"
}
```

### 404 Not Found
```json
{
  "detail": "incident not found"
}
```

---

## Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request |
| 404 | Not found |
| 500 | Server error |

---

## Rate Limiting

Not currently implemented. Add in production with middleware:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/ingest")
@limiter.limit("100/minute")
def api_ingest(record: LogRecord):
    ...
```

---

## Authentication

Not currently implemented. Add API key auth:
```python
from fastapi.security import APIKeyHeader
api_key_header = APIKeyHeader(name="X-API-Key")

@app.post("/ingest")
def api_ingest(record: LogRecord, api_key: str = Depends(api_key_header)):
    ...
```
