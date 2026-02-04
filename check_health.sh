#!/usr/bin/env bash
# check_health.sh - myTIME Health Check Script

set -e

echo "🏥 Checking myTIME Service Health..."
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_service() {
    local service_name=$1
    local health_url=$2
    local container_name=$3
    
    echo -n "Checking $service_name... "
    
    # First check if container is running
    if ! docker ps | grep -q "$container_name"; then
        echo -e "${RED}CONTAINER DOWN${NC}"
        return 1
    fi
    
    # Then check health endpoint
    if curl -sf "$health_url" > /dev/null 2>&1; then
        echo -e "${GREEN}ACTIVE${NC}"
        return 0
    else
        echo -e "${YELLOW}NO RESPONSE${NC}"
        return 1
    fi
}

# Check each service
check_service "Foreman (Triage)" "http://localhost:8080/health" "gauntlet-foreman-triage"
check_service "Actor (Service)" "http://localhost:8000/health" "gauntlet-actor-service"
check_service "Architect" "http://localhost:5000/health" "gauntlet-architect"
check_service "Auditor" "http://localhost:5001/health" "gauntlet-auditor"
check_service "Steward" "http://localhost:8080/health" "gauntlet-steward"

echo ""
echo "Checking Ollama (Actor Backend)..."
if docker ps | grep -q "gauntlet-actor"; then
    echo -e "${GREEN}Ollama container is running${NC}"
else
    echo -e "${RED}Ollama container is down${NC}"
fi

echo ""
echo "Checking Asterisk (Foreman SIP)..."
if docker ps | grep -q "gauntlet-foreman"; then
    echo -e "${GREEN}Asterisk container is running${NC}"
else
    echo -e "${RED}Asterisk container is down${NC}"
fi

echo ""
echo "📊 Quick Stats:"
echo "   - Directory Structure: $([ -d learning_repo ] && echo -e '${GREEN}✓${NC}' || echo -e '${RED}✗${NC}')"
echo "   - Master Key: $([ -f config/master.key ] && echo -e '${GREEN}✓${NC}' || echo -e '${RED}✗${NC}')"
echo "   - Config File: $([ -f config/settings.yaml ] && echo -e '${GREEN}✓${NC}' || echo -e '${RED}✗${NC}')"

echo ""
echo "🛡️ The Building Crew status check complete."
echo "   For detailed logs: docker compose logs [service-name]"
