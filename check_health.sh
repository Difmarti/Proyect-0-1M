#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Checking service health...${NC}"

# Check Docker services
services=("trading_timescaledb" "trading_redis" "trading_bridge" "trading_api" "trading_dashboard" "trading_portainer")
all_healthy=true

for service in "${services[@]}"; do
    echo -e "\n${YELLOW}Checking $service${NC}"
    
    # Check if container exists and is running
    if ! docker ps -q -f name=^/${service}$ >/dev/null 2>&1; then
        echo -e "${RED}Service $service is not running${NC}"
        all_healthy=false
        continue
    fi

    # Check container health
    health_status=$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null)
    if [ "$health_status" != "healthy" ]; then
        echo -e "${RED}Service $service is not healthy (Status: $health_status)${NC}"
        echo -e "${YELLOW}Last 3 health check logs:${NC}"
        docker inspect --format='{{range .State.Health.Log}}{{println .Output}}{{end}}' "$service" | tail -n 3
        all_healthy=false
    else
        echo -e "${GREEN}Service $service is healthy${NC}"
    fi

    # Show resource usage
    echo -e "\nResource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" "$service"
done

# Show recent logs if service is unhealthy
if [ "$all_healthy" = false ]; then
    echo -e "\n${RED}Some services are not healthy. Recent logs:${NC}"
    for service in "${services[@]}"; do
        if [ "$(docker inspect --format='{{.State.Health.Status}}' "$service" 2>/dev/null)" != "healthy" ]; then
            echo -e "\n${YELLOW}=== $service logs ===${NC}"
            docker logs --tail 10 "$service"
        fi
    done
fi

# Show system resource usage
echo -e "\n${YELLOW}System Resource Usage:${NC}"
echo "CPU Usage:"
top -bn1 | grep "Cpu(s)" | sed "s/.*, *\([0-9.]*\)%* id.*/\1/" | awk '{print 100 - $1"%"}'
echo -e "\nMemory Usage:"
free -h

# Check disk space
echo -e "\n${YELLOW}Disk Space:${NC}"
df -h /

if [ "$all_healthy" = false ]; then
    echo -e "\n${RED}Some services are unhealthy. Please check the logs above for details.${NC}"
    exit 1
else
    echo -e "\n${GREEN}All services are healthy!${NC}"
fi