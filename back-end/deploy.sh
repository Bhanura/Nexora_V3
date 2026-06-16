#!/bin/bash

# eLanka Chat AI Deployment Script
# Pulls latest code from GitHub and restarts Docker containers

set -e  # Exit on error

echo "🚀 eLanka Chat AI Deployment Script"
echo "================================"

# Configuration
REPO_DIR="/root/eLanka_Chat_AI"
BRANCH="main"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Navigate to repository
echo -e "${YELLOW}[1/6]${NC} Navigating to repository..."
cd "$REPO_DIR" || exit 1

# Step 2: Pull latest code
echo -e "${YELLOW}[2/6]${NC} Pulling latest code from GitHub..."
git fetch origin
git reset --hard origin/$BRANCH
echo -e "${GREEN}✓${NC} Code updated"

# Step 3: Stop running containers
echo -e "${YELLOW}[3/6]${NC} Stopping containers..."
docker-compose down
echo -e "${GREEN}✓${NC} Containers stopped"

# Step 4: Build new images
echo -e "${YELLOW}[4/6]${NC} Building Docker images..."
docker-compose build --no-cache
echo -e "${GREEN}✓${NC} Images built"

# Step 5: Start containers
echo -e "${YELLOW}[5/6]${NC} Starting containers..."
docker-compose up -d
echo -e "${GREEN}✓${NC} Containers started"

# Step 6: Show status
echo -e "${YELLOW}[6/6]${NC} Checking container status..."
docker-compose ps

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check health
if curl -f http://localhost:8000/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend is healthy"
else
    echo -e "${RED}✗${NC} Backend health check failed"
fi

if curl -f http://localhost:6333/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Qdrant is healthy"
else
    echo -e "${RED}✗${NC} Qdrant health check failed"
fi

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "View logs: docker-compose logs -f"
echo "Stop: docker-compose down"
echo "Restart: docker-compose restart"
