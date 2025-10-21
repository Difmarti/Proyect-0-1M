#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if backup file is provided
if [ -z "$1" ]; then
    echo -e "${RED}Error: No backup file specified${NC}"
    echo "Usage: ./restore.sh <backup_file.tar.gz>"
    exit 1
fi

BACKUP_FILE="$1"
TEMP_DIR="/tmp/trading_restore_$$"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}Error: Backup file not found: $BACKUP_FILE${NC}"
    exit 1
fi

# Create temporary directory
mkdir -p "$TEMP_DIR"

echo -e "${YELLOW}Starting restore process...${NC}"

# Extract backup
echo -e "${YELLOW}Extracting backup files...${NC}"
tar -xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Stop services
echo -e "${YELLOW}Stopping services...${NC}"
docker-compose down

# Restore PostgreSQL database
echo -e "${YELLOW}Restoring PostgreSQL database...${NC}"
cat "$TEMP_DIR"/db_backup_*.sql | docker-compose exec -T timescaledb psql -U "${POSTGRES_USER}" "${POSTGRES_DB}"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Database restore completed successfully${NC}"
else
    echo -e "${RED}Database restore failed${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Restore Redis data
echo -e "${YELLOW}Restoring Redis data...${NC}"
docker cp "$TEMP_DIR"/redis_backup_*.rdb trading_redis:/data/dump.rdb
docker-compose exec -T redis redis-cli SHUTDOWN SAVE

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Redis restore completed successfully${NC}"
else
    echo -e "${RED}Redis restore failed${NC}"
    rm -rf "$TEMP_DIR"
    exit 1
fi

# Start services
echo -e "${YELLOW}Starting services...${NC}"
docker-compose up -d

# Clean up
rm -rf "$TEMP_DIR"

echo -e "${GREEN}Restore completed successfully!${NC}"
echo -e "\nTo check service health: ./check_health.sh"