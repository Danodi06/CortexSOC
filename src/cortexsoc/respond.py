"""Response automation with action tracking and mock integrations."""
from typing import Dict, Any, List
import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger("cortexsoc.respond")


class ActionStatus(str, Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


# In-memory incident log
_incidents: List[Dict[str, Any]] = []
_incident_counter = 0


class Incident:
    """Track a single security incident and its responses."""
    
    def __init__(self, alert_id: str, alert_reason: str, user: str = None, ip: str = None):
        global _incident_counter
        _incident_counter += 1
        self.id = _incident_counter
        self.alert_id = alert_id
        self.alert_reason = alert_reason
        self.user = user
        self.ip = ip
        self.created_at = datetime.utcnow().isoformat() + "Z"
        self.actions: List[Dict[str, Any]] = []
        self.status = "active"
    
    def add_action(self, action: str, target: str, status: str, details: str = ""):
        self.actions.append({
            "action": action,
            "target": target,
            "status": status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "details": details,
        })
    
    def to_dict(self):
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "alert_reason": self.alert_reason,
            "user": self.user,
            "ip": self.ip,
            "created_at": self.created_at,
            "status": self.status,
            "actions": self.actions,
        }


def create_incident(alert: Dict[str, Any]) -> Incident:
    """Create a new incident from an alert."""
    incident = Incident(
        alert_id=str(alert.get("id", "unknown")),
        alert_reason=alert.get("reason", "unknown"),
        user=alert.get("user"),
        ip=alert.get("ip"),
    )
    _incidents.append(incident)
    logger.info(f"Created incident #{incident.id} for {alert.get('reason')}")
    return incident


def block_ip(ip: str, incident: Incident = None) -> Dict[str, Any]:
    """Block an IP address (mock firewall integration)."""
    logger.info(f"Blocking IP: {ip}")
    
    # Mock: In production, this would call a firewall API
    status = ActionStatus.SUCCESS
    details = f"IP {ip} added to blocklist (mock action)"
    
    if incident:
        incident.add_action("block_ip", ip, status, details)
    
    return {"action": "block_ip", "ip": ip, "status": status, "details": details}


def disable_account(user: str, incident: Incident = None) -> Dict[str, Any]:
    """Disable a user account (mock IAM integration)."""
    logger.info(f"Disabling account: {user}")
    
    # Mock: In production, this would call an IAM API
    status = ActionStatus.SUCCESS
    details = f"User {user} account disabled (mock action)"
    
    if incident:
        incident.add_action("disable_account", user, status, details)
    
    return {"action": "disable_account", "user": user, "status": status, "details": details}


def send_alert(channel: str, message: str, incident: Incident = None) -> Dict[str, Any]:
    """Send an alert to Slack/Email/Teams (mock notification)."""
    logger.info(f"Alert to {channel}: {message}")
    
    # Mock: In production, this would integrate with Slack SDK, etc.
    status = ActionStatus.SUCCESS
    details = f"Alert sent to {channel}: {message}"
    
    if incident:
        incident.add_action("alert", channel, status, details)
    
    return {"action": "alert", "channel": channel, "status": status, "details": details}


def auto_respond_to_alert(alert: Dict[str, Any]) -> Incident:
    """Auto-respond to an alert based on severity and type."""
    incident = create_incident(alert)
    severity = alert.get("severity", "low")
    reason = alert.get("reason", "")
    user = alert.get("user")
    ip = alert.get("ip")
    
    # Response playbook
    if severity == "high":
        if reason == "failed_login_threshold" and user:
            disable_account(user, incident)
            send_alert("ops", f"High: Disabled account {user} due to failed login threshold", incident)
        if ip:
            block_ip(ip, incident)
            send_alert("ops", f"High: Blocked IP {ip}", incident)
    
    elif severity == "medium":
        send_alert("security", f"Medium: {reason} - User: {user}, IP: {ip}", incident)
    
    else:  # low
        send_alert("logs", f"Low: {reason}", incident)
    
    return incident


def get_incidents() -> List[Dict[str, Any]]:
    """Return all incidents."""
    return [i.to_dict() for i in _incidents]


def get_incident(incident_id: int) -> Dict[str, Any]:
    """Get a specific incident."""
    for i in _incidents:
        if i.id == incident_id:
            return i.to_dict()
    return None
