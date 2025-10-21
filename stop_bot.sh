#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Stopping trading bot services...${NC}"

# Stop Docker services
docker-compose down

# Check if any containers are still running
if docker ps | grep -q "trading_"; then
    echo -e "${RED}Some containers are still running. Forcing stop...${NC}"
    docker-compose down -v --remove-orphans
fi

echo -e "${GREEN}Trading bot stopped successfully!${NC}"
echo -e "\nTo start services again: ./start_bot.sh"