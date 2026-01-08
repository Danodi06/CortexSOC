#!/usr/bin/env bash
# CortexSOC Live Demo Script
# Run this to see CortexSOC in action with realistic attack scenarios

BASE_URL="http://127.0.0.1:8000"

echo "=========================================="
echo "  CortexSOC Live Demo"
echo "=========================================="
echo

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Demo 1: Simulating Brute Force Attack${NC}"
echo "Sending 6 failed login attempts for user 'attacker'..."
for i in {1..6}; do
    curl -s -X POST "$BASE_URL/ingest" \
        -H "Content-Type: application/json" \
        -d "{\"type\": \"failed_login\", \"user\": \"attacker\", \"ip\": \"203.0.113.1\"}" > /dev/null
    echo "  Failed attempt $i ✓"
done
echo

echo -e "${GREEN}Demo 2: Detecting the Attack${NC}"
echo "Running threat detection..."
curl -s "$BASE_URL/detect" | python -m json.tool | head -50
echo

echo -e "${GREEN}Demo 3: Simulating Impossible Travel${NC}"
echo "Same user logs in from two countries within seconds..."
curl -s -X POST "$BASE_URL/ingest" \
    -H "Content-Type: application/json" \
    -d '{"type": "login", "user": "traveler", "origin": "US", "ip": "203.0.113.5"}' > /dev/null
echo "  Login from US ✓"

curl -s -X POST "$BASE_URL/ingest" \
    -H "Content-Type: application/json" \
    -d '{"type": "login", "user": "traveler", "origin": "CN", "ip": "203.0.113.6"}' > /dev/null
echo "  Login from China (1 second later) ✓"
echo

echo -e "${GREEN}Demo 4: Auto-Response in Action${NC}"
echo "Running detection with automatic response..."
curl -s -X POST "$BASE_URL/detect-and-respond" | python -m json.tool | head -100
echo

echo -e "${GREEN}Demo 5: Viewing All Incidents${NC}"
echo "Retrieving all security incidents..."
curl -s "$BASE_URL/incidents" | python -m json.tool | head -50
echo

echo -e "${YELLOW}Demo Complete!${NC}"
echo
echo "Next steps:"
echo "  1. Visit the dashboard: http://127.0.0.1:8000/static/index.html"
echo "  2. Click 'Run Detection' to see real-time alerts"
echo "  3. Click 'Detect & Respond' to trigger auto-response"
echo
echo "API Documentation: Check API.md for full endpoint reference"
