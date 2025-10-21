#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Starting trading bot services...${NC}"

# Start Docker services
docker-compose up -d

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 10

# Check service health
./check_health.sh

# If health check passed, show access information
if [ $? -eq 0 ]; then
    echo -e "\n${GREEN}Trading bot started successfully!${NC}"
    echo -e "\nAccess points:"
    echo -e "Dashboard: http://localhost:8501"
    echo -e "API Docs:  http://localhost:8000/docs"
    echo -e "Portainer: http://localhost:9000"
    echo -e "\nTo check health: ./check_health.sh"
    echo -e "To view logs: docker-compose logs -f"
    echo -e "To stop services: ./stop_bot.sh"
else
    echo -e "\n${RED}Some services failed to start properly. Please check the logs above.${NC}"
fi