#!/bin/bash

# Trading Bot Installation Script
# Automated setup for MT5 trading bot on Ubuntu 22.04 LTS

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Script info
echo -e "${BLUE}================================================${NC}"
echo -e "${BLUE}  MT5 Trading Bot - Installation Script${NC}"
echo -e "${BLUE}================================================${NC}\n"

# Function to print section headers
print_section() {
    echo -e "\n${BLUE}>>> $1${NC}"
}

# Function to print success messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error messages
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print warning messages
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to check if a port is available
check_port() {
    if ss -tuln | grep -q ":$1 "; then
        print_error "Port $1 is already in use"
        return 1
    fi
    return 0
}

# Function to check RAM
check_ram() {
    total_ram=$(free -g | awk '/^Mem:/{print $2}')
    if [ "$total_ram" -lt 6 ]; then
        print_warning "System has ${total_ram}GB RAM. Recommended: 6GB+"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    else
        print_success "RAM check passed (${total_ram}GB available)"
    fi
}

# STEP 1: Verify Prerequisites
print_section "Step 1: Verifying Prerequisites"

# Check Ubuntu version
if [ -f /etc/os-release ]; then
    . /etc/os-release
    if [[ "$ID" == "ubuntu" ]]; then
        print_success "Running on Ubuntu $VERSION"
    else
        print_warning "Not running on Ubuntu. This script is designed for Ubuntu 22.04 LTS"
    fi
else
    print_warning "Cannot determine OS version"
fi

# Check RAM
check_ram

# Check Docker
print_section "Checking Docker installation"
if ! docker version > /dev/null 2>&1; then
    print_error "Docker is not installed or not running"
    print_warning "Please install Docker first: https://docs.docker.com/engine/install/ubuntu/"
    exit 1
else
    docker_version=$(docker --version | cut -d ' ' -f3 | tr -d ',')
    print_success "Docker $docker_version installed"
fi

# Check Docker Compose
print_section "Checking Docker Compose installation"
docker compose version > /dev/null 2>&1
COMPOSE_V2=$?
if [ $COMPOSE_V2 -eq 0 ]; then
    compose_version=$(docker compose version --short)
    print_success "Docker Compose V2 ($compose_version) installed"
    COMPOSE_CMD="docker compose"
elif docker-compose --version > /dev/null 2>&1; then
    compose_version=$(docker-compose --version | cut -d ' ' -f3 | tr -d ',')
    print_success "Docker Compose V1 ($compose_version) installed"
    COMPOSE_CMD="docker-compose"
else
    print_error "Docker Compose is not installed"
    exit 1
fi

# Check ports
print_section "Checking port availability"
required_ports=(5432 6379 8080 8501)
all_ports_free=true

for port in "${required_ports[@]}"; do
    if check_port "$port"; then
        print_success "Port $port is available"
    else
        all_ports_free=false
    fi
done

if [ "$all_ports_free" = false ]; then
    print_error "Some required ports are in use. Please free them before continuing."
    exit 1
fi

# STEP 2: Create Project Structure
print_section "Step 2: Creating Project Structure"

# Create necessary directories
directories=(
    "postgres/data"
    "python-bridge/logs"
    "api/logs"
    "dashboard/logs"
    "metatrader5/config"
    "backups"
)

for dir in "${directories[@]}"; do
    mkdir -p "$dir"
    print_success "Created directory: $dir"
done

# STEP 3: Configure Environment
print_section "Step 3: Configuring Environment Variables"

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        print_success "Created .env file from .env.example"

        # Generate secure PostgreSQL password
        PG_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        sed -i "s/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$PG_PASSWORD/" .env
        print_success "Generated secure PostgreSQL password"

        print_warning "Please edit .env file with your MT5 credentials:"
        echo -e "  - MT5_ACCOUNT"
        echo -e "  - MT5_PASSWORD"
        echo -e "  - MT5_SERVER"
        echo ""
        read -p "Press Enter when done editing .env file..."
    else
        print_error ".env.example not found!"
        exit 1
    fi
else
    print_success ".env file already exists"
fi

# STEP 4: Build and Start Services
print_section "Step 4: Building and Starting Docker Services"

echo "This may take several minutes on first run..."

# Pull base images first
print_section "Pulling base Docker images"
$COMPOSE_CMD pull timescaledb redis 2>&1 | grep -E "(Pulling|Downloaded|Status)" || true

# Build custom images
print_section "Building custom service images"
$COMPOSE_CMD build --no-cache

# Start services
print_section "Starting services"
$COMPOSE_CMD up -d

# STEP 5: Wait for Services
print_section "Step 5: Waiting for Services to Initialize"

echo "Waiting 60 seconds for services to start..."
for i in {60..1}; do
    echo -ne "\rTime remaining: ${i}s "
    sleep 1
done
echo -e "\n"

# STEP 6: Health Checks
print_section "Step 6: Performing Health Checks"

services=("trading_timescaledb" "trading_redis" "trading_mt5" "trading_bridge" "trading_api" "trading_dashboard")
all_healthy=true

for service in "${services[@]}"; do
    # Check if container is running
    if docker ps --format '{{.Names}}' | grep -q "^${service}$"; then
        # Check health status
        health_status=$(docker inspect --format='{{if .State.Health}}{{.State.Health.Status}}{{else}}no healthcheck{{end}}' "$service" 2>/dev/null)

        if [ "$health_status" = "healthy" ]; then
            print_success "$service is healthy"
        elif [ "$health_status" = "no healthcheck" ]; then
            # Check if running at least
            state=$(docker inspect --format='{{.State.Status}}' "$service")
            if [ "$state" = "running" ]; then
                print_success "$service is running (no healthcheck defined)"
            else
                print_error "$service is not running (state: $state)"
                all_healthy=false
            fi
        else
            print_warning "$service status: $health_status (may still be starting)"
            all_healthy=false
        fi
    else
        print_error "$service is not running"
        all_healthy=false
    fi
done

# STEP 7: Database Verification
print_section "Step 7: Verifying Database Setup"

if docker exec trading_timescaledb pg_isready -U trading_user -d trading_db > /dev/null 2>&1; then
    print_success "TimescaleDB is ready"

    # Check if tables exist
    table_count=$(docker exec trading_timescaledb psql -U trading_user -d trading_db -t -c "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | tr -d ' ')

    if [ "$table_count" -gt 0 ]; then
        print_success "Database tables initialized ($table_count tables found)"
    else
        print_warning "Database tables not found. They should be created automatically."
    fi
else
    print_error "Cannot connect to TimescaleDB"
    all_healthy=false
fi

# STEP 8: Final Summary
print_section "Installation Summary"

if [ "$all_healthy" = true ]; then
    echo -e "${GREEN}================================================${NC}"
    echo -e "${GREEN}  Installation completed successfully! ✓${NC}"
    echo -e "${GREEN}================================================${NC}\n"

    echo -e "${BLUE}Access Points:${NC}"
    echo -e "  Dashboard:  ${GREEN}http://localhost:8501${NC}"
    echo -e "  API Docs:   ${GREEN}http://localhost:8080/docs${NC}"

    echo -e "\n${BLUE}Management Commands:${NC}"
    echo -e "  Start:      ${YELLOW}./start_bot.sh${NC}"
    echo -e "  Stop:       ${YELLOW}./stop_bot.sh${NC}"
    echo -e "  Health:     ${YELLOW}./check_health.sh${NC}"
    echo -e "  Backup:     ${YELLOW}./backup.sh${NC}"
    echo -e "  Logs:       ${YELLOW}docker compose logs -f [service]${NC}"

    echo -e "\n${BLUE}Next Steps:${NC}"
    echo -e "  1. Verify MT5 credentials in .env file"
    echo -e "  2. Check MT5 connection: ${YELLOW}docker logs trading_mt5${NC}"
    echo -e "  3. Monitor trading bridge: ${YELLOW}docker logs -f trading_bridge${NC}"
    echo -e "  4. Access dashboard to verify data flow"

else
    echo -e "${YELLOW}================================================${NC}"
    echo -e "${YELLOW}  Installation completed with warnings${NC}"
    echo -e "${YELLOW}================================================${NC}\n"

    print_warning "Some services are not fully healthy yet"
    echo -e "\n${BLUE}Troubleshooting:${NC}"
    echo -e "  View logs:  ${YELLOW}docker compose logs -f [service_name]${NC}"
    echo -e "  Restart:    ${YELLOW}docker compose restart [service_name]${NC}"
    echo -e "  Rebuild:    ${YELLOW}docker compose up -d --build [service_name]${NC}"

    echo -e "\n${BLUE}Check individual service logs:${NC}"
    for service in "${services[@]}"; do
        echo -e "  ${YELLOW}docker logs $service${NC}"
    done
fi

echo ""