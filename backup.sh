#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Create backup directory if it doesn't exist
BACKUP_DIR="./backups"
mkdir -p "$BACKUP_DIR"

# Generate timestamp for backup files
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

echo -e "${YELLOW}Starting backup process...${NC}"

# Backup PostgreSQL database
echo -e "${YELLOW}Backing up PostgreSQL database...${NC}"
docker-compose exec -T timescaledb pg_dump -U "${POSTGRES_USER}" "${POSTGRES_DB}" > "${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Database backup completed successfully${NC}"
else
    echo -e "${RED}Database backup failed${NC}"
    exit 1
fi

# Backup Redis data
echo -e "${YELLOW}Backing up Redis data...${NC}"
docker-compose exec -T redis redis-cli save
docker cp trading_redis:/data/dump.rdb "${BACKUP_DIR}/redis_backup_${TIMESTAMP}.rdb"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Redis backup completed successfully${NC}"
else
    echo -e "${RED}Redis backup failed${NC}"
    exit 1
fi

# Compress backups
echo -e "${YELLOW}Compressing backup files...${NC}"
tar -czf "${BACKUP_DIR}/full_backup_${TIMESTAMP}.tar.gz" \
    "${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql" \
    "${BACKUP_DIR}/redis_backup_${TIMESTAMP}.rdb"

# Clean up temporary files
rm "${BACKUP_DIR}/db_backup_${TIMESTAMP}.sql" "${BACKUP_DIR}/redis_backup_${TIMESTAMP}.rdb"

# Remove backups older than 7 days
find "${BACKUP_DIR}" -name "full_backup_*.tar.gz" -mtime +7 -delete

echo -e "${GREEN}Backup completed successfully!${NC}"
echo -e "Backup location: ${BACKUP_DIR}/full_backup_${TIMESTAMP}.tar.gz"
echo -e "\nTo restore this backup: ./restore.sh ${BACKUP_DIR}/full_backup_${TIMESTAMP}.tar.gz"