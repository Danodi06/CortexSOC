"""Detection routines with rule-based and ML-based anomaly detection."""
from typing import List, Dict, Any
from collections import defaultdict
from datetime import datetime
import logging

logger = logging.getLogger("cortexsoc.detect")

# Stateful tracking: seen origins per user, failed logins, etc.
_seen_origins = defaultdict(set)
_failed_logins = defaultdict(int)
_user_login_times = defaultdict(list)


def rule_login_from_new_origin(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect logins from a new country/origin not seen before for the user.

    Severity: medium (new origin is unusual but not necessarily malicious).
    """
    alerts = []
    for r in logs:
        if r.get("type") != "login":
            continue
        user = r.get("user")
        origin = r.get("origin")
        if not user or not origin:
            continue
        if origin not in _seen_origins[user]:
            alerts.append({
                "user": user,
                "origin": origin,
                "reason": "new_origin",
                "severity": "medium",
                "record": r,
            })
            _seen_origins[user].add(origin)
    return alerts


def rule_failed_login_threshold(logs: List[Dict[str, Any]], threshold: int = 5) -> List[Dict[str, Any]]:
    """Detect excessive failed login attempts for a user.

    Severity: high (many failed attempts suggest brute force).
    """
    alerts = []
    for r in logs:
        if r.get("type") != "failed_login":
            continue
        user = r.get("user")
        if not user:
            continue
        _failed_logins[user] += 1
        if _failed_logins[user] >= threshold:
            alerts.append({
                "user": user,
                "reason": "failed_login_threshold",
                "severity": "high",
                "failed_count": _failed_logins[user],
                "record": r,
            })
    return alerts


def rule_login_unusual_time(logs: List[Dict[str, Any]], outside_hours: tuple = (22, 6)) -> List[Dict[str, Any]]:
    """Detect logins outside normal business hours.

    Severity: low (may indicate off-hours activity, needs context).
    """
    alerts = []
    for r in logs:
        if r.get("type") != "login":
            continue
        user = r.get("user")
        timestamp_str = r.get("timestamp")
        if not user or not timestamp_str:
            continue
        try:
            ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            hour = ts.hour
            if hour >= outside_hours[0] or hour < outside_hours[1]:
                alerts.append({
                    "user": user,
                    "reason": "unusual_login_time",
                    "severity": "low",
                    "hour": hour,
                    "record": r,
                })
        except Exception:
            pass
    return alerts


def rule_rapid_multiple_logins(logs: List[Dict[str, Any]], window_seconds: int = 60) -> List[Dict[str, Any]]:
    """Detect multiple logins for the same user within a short window.

    Severity: medium (may indicate compromised account or scripted activity).
    """
    alerts = []
    user_login_times = defaultdict(list)
    
    for r in logs:
        if r.get("type") != "login":
            continue
        user = r.get("user")
        timestamp_str = r.get("timestamp")
        if not user or not timestamp_str:
            continue
        try:
            ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            user_login_times[user].append(ts)
        except Exception:
            pass
    
    for user, times in user_login_times.items():
        times.sort()
        for i in range(len(times) - 1):
            delta = (times[i + 1] - times[i]).total_seconds()
            if 0 < delta < window_seconds:
                alerts.append({
                    "user": user,
                    "reason": "rapid_logins",
                    "severity": "medium",
                    "logins_in_window": len(times),
                    "window_seconds": window_seconds,
                    "record": times[i].__dict__ if hasattr(times[i], '__dict__') else None,
                })
                break
    
    return alerts


def detect_all(logs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Run all detection rules and return aggregated alerts.

    Alerts include severity levels (low, medium, high) for prioritization.
    """
    results = []
    results.extend(rule_login_from_new_origin(logs))
    results.extend(rule_failed_login_threshold(logs))
    results.extend(rule_login_unusual_time(logs))
    results.extend(rule_rapid_multiple_logins(logs))
    
    # Sort by severity
    severity_order = {"high": 0, "medium": 1, "low": 2}
    results.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 3))
    
    return results
