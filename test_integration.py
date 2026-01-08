#!/usr/bin/env python3
"""
Simple integration test for CortexSOC.

Run this script to verify the full workflow: ingest → detect → respond.
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 5

# Allow override via environment
import os
if os.getenv("CORTEXSOC_URL"):
    BASE_URL = os.getenv("CORTEXSOC_URL")


def print_section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def test_health():
    """Test 1: Server health check."""
    print_section("Test 1: Health Check")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        resp.raise_for_status()
        print(f"[OK] Health check passed: {resp.json()}")
        return True
    except Exception as e:
        print(f"[FAIL] Health check failed: {e}")
        return False


def test_ingestion():
    """Test 2: Log ingestion."""
    print_section("Test 2: Log Ingestion")
    
    test_logs = [
        {"type": "login", "user": "alice", "origin": "US", "ip": "1.2.3.4"},
        {"type": "login", "user": "alice", "origin": "UK", "ip": "5.6.7.8"},
        {"type": "failed_login", "user": "bob", "ip": "10.0.0.1"},
        {"type": "failed_login", "user": "bob", "ip": "10.0.0.2"},
        {"type": "failed_login", "user": "bob", "ip": "10.0.0.3"},
        {"type": "failed_login", "user": "bob", "ip": "10.0.0.4"},
        {"type": "failed_login", "user": "bob", "ip": "10.0.0.5"},
    ]
    
    try:
        for log in test_logs:
            resp = requests.post(f"{BASE_URL}/ingest", json=log, timeout=TIMEOUT)
            resp.raise_for_status()
        print(f"[OK] Ingested {len(test_logs)} logs successfully")
        return True
    except Exception as e:
        print(f"[FAIL] Ingestion failed: {e}")
        return False


def test_detection():
    """Test 3: Run detection."""
    print_section("Test 3: Threat Detection")
    try:
        resp = requests.get(f"{BASE_URL}/detect", timeout=TIMEOUT)
        resp.raise_for_status()
        alerts = resp.json()
        print(f"[OK] Detection completed, found {len(alerts)} alerts:")
        
        for alert in alerts:
            severity = alert.get("severity", "unknown")
            reason = alert.get("reason", "unknown")
            user = alert.get("user", "N/A")
            print(f"  - [{severity.upper()}] {reason} (User: {user})")
        
        return len(alerts) > 0
    except Exception as e:
        print(f"[FAIL] Detection failed: {e}")
        return False


def test_auto_response():
    """Test 4: Detect and auto-respond."""
    print_section("Test 4: Auto-Response")
    try:
        resp = requests.post(f"{BASE_URL}/detect-and-respond", timeout=TIMEOUT)
        resp.raise_for_status()
        result = resp.json()
        
        print(f"[OK] Auto-response executed:")
        print(f"  - Alerts generated: {result['alerts_generated']}")
        print(f"  - Incidents created: {result['incidents_created']}")
        
        for incident in result.get("incidents", [])[:3]:  # Show first 3
            print(f"\n  Incident #{incident['id']}: {incident['alert_reason']}")
            for action in incident.get("actions", []):
                print(f"    -> {action['action']}: {action['target']} ({action['status']})")
        
        return True
    except Exception as e:
        print(f"[FAIL] Auto-response failed: {e}")
        return False


def test_incidents_api():
    """Test 5: Incidents API."""
    print_section("Test 5: Incidents API")
    try:
        # Get all incidents
        resp = requests.get(f"{BASE_URL}/incidents", timeout=TIMEOUT)
        resp.raise_for_status()
        incidents = resp.json()
        print(f"[OK] Retrieved {len(incidents)} incidents")
        
        if incidents:
            # Get specific incident
            incident_id = incidents[0]["id"]
            resp = requests.get(f"{BASE_URL}/incidents/{incident_id}", timeout=TIMEOUT)
            resp.raise_for_status()
            incident = resp.json()
            print(f"[OK] Retrieved incident #{incident_id} details")
            print(f"  - Alert: {incident['alert_reason']}")
            print(f"  - User: {incident['user']}")
            print(f"  - Actions: {len(incident['actions'])}")
        
        return True
    except Exception as e:
        print(f"[FAIL] Incidents API failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  CortexSOC Integration Test Suite")
    print("="*60)
    
    tests = [
        test_health,
        test_ingestion,
        test_detection,
        test_auto_response,
        test_incidents_api,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print_section("Test Summary")
    passed = sum(results)
    total = len(results)
    print(f"\nPassed: {passed}/{total} tests")
    
    if passed == total:
        print("\n[ALL TESTS PASSED]")
        return 0
    else:
        print(f"\n[{total - passed} test(s) failed]")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
