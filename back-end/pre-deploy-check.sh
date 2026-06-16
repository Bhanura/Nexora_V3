#!/bin/bash

# Production Deployment Pre-flight Checklist Script
# Run this BEFORE deploying to server

set -e

echo "🔍 Nexora001 Production Deployment Checklist"
echo "=============================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check counter
WARNINGS=0
ERRORS=0

# Function to check .env file
check_env_file() {
    echo -e "${YELLOW}[CHECK 1]${NC} Checking .env file..."
    
    if [ ! -f ".env" ]; then
        echo -e "${RED}❌ .env file not found!${NC}"
        echo "   Run: cp .env.example .env"
        ((ERRORS++))
        return
    fi
    
    # Check for default/weak values
    if grep -q "changeme123" .env; then
        echo -e "${RED}❌ Found default password 'changeme123' in .env${NC}"
        echo "   Generate strong password: openssl rand -base64 32"
        ((ERRORS++))
    fi
    
    if grep -q "your-secret-key-change-in-production" .env; then
        echo -e "${RED}❌ Found default JWT secret in .env${NC}"
        echo "   Generate strong secret: openssl rand -hex 32"
        ((ERRORS++))
    fi
    
    if grep -q "your_api_key_here" .env; then
        echo -e "${RED}❌ Found placeholder Google API key in .env${NC}"
        echo "   Get real API key from: https://aistudio.google.com/apikey"
        ((ERRORS++))
    fi
    
    # Check environment setting
    if grep -q "ENVIRONMENT=development" .env; then
        echo -e "${YELLOW}⚠️  ENVIRONMENT is set to 'development'${NC}"
        echo "   For production server, change to: ENVIRONMENT=production"
        ((WARNINGS++))
    fi
    
    if grep -q "DEBUG=true" .env; then
        echo -e "${YELLOW}⚠️  DEBUG is set to 'true'${NC}"
        echo "   For production server, change to: DEBUG=false"
        ((WARNINGS++))
    fi
    
    if [ $ERRORS -eq 0 ]; then
        echo -e "${GREEN}✓ .env file configured${NC}"
    fi
}

# Check Git status
check_git_status() {
    echo ""
    echo -e "${YELLOW}[CHECK 2]${NC} Checking Git status..."
    
    if [ -n "$(git status --porcelain)" ]; then
        echo -e "${YELLOW}⚠️  You have uncommitted changes:${NC}"
        git status --short
        echo ""
        echo "   Commit and push before deploying to server:"
        echo "   git add ."
        echo "   git commit -m 'Your message'"
        echo "   git push origin main"
        ((WARNINGS++))
    else
        echo -e "${GREEN}✓ All changes committed${NC}"
    fi
    
    # Check if pushed
    LOCAL=$(git rev-parse @)
    REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")
    
    if [ -n "$REMOTE" ] && [ "$LOCAL" != "$REMOTE" ]; then
        echo -e "${YELLOW}⚠️  Local commits not pushed to GitHub${NC}"
        echo "   Run: git push origin main"
        ((WARNINGS++))
    elif [ -n "$REMOTE" ]; then
        echo -e "${GREEN}✓ All commits pushed to GitHub${NC}"
    fi
}

# Check required files
check_required_files() {
    echo ""
    echo -e "${YELLOW}[CHECK 3]${NC} Checking required files..."
    
    REQUIRED_FILES=(
        "docker-compose.yml"
        "Dockerfile"
        "deploy.sh"
        "nginx/default.conf"
        "../Nexora001_Frontend/Dockerfile"
    )
    
    for file in "${REQUIRED_FILES[@]}"; do
        if [ ! -f "$file" ]; then
            echo -e "${RED}❌ Missing file: $file${NC}"
            ((ERRORS++))
        fi
    done
    
    if [ $ERRORS -eq 0 ]; then
        echo -e "${GREEN}✓ All required files present${NC}"
    fi
}

# Check deploy.sh permissions
check_deploy_script() {
    echo ""
    echo -e "${YELLOW}[CHECK 4]${NC} Checking deploy.sh..."
    
    if [ ! -x "deploy.sh" ]; then
        echo -e "${YELLOW}⚠️  deploy.sh is not executable${NC}"
        echo "   Run: chmod +x deploy.sh"
        ((WARNINGS++))
    else
        echo -e "${GREEN}✓ deploy.sh is executable${NC}"
    fi
}

# Check Docker locally
check_docker() {
    echo ""
    echo -e "${YELLOW}[CHECK 5]${NC} Checking Docker setup..."
    
    if ! command -v docker &> /dev/null; then
        echo -e "${YELLOW}⚠️  Docker not found (only needed for local testing)${NC}"
    else
        echo -e "${GREEN}✓ Docker installed${NC}"
        
        # Check if images exist
        if docker images | grep -q "nexora001"; then
            echo -e "${GREEN}✓ Nexora001 Docker images exist${NC}"
        else
            echo -e "${YELLOW}⚠️  No Nexora001 images found (run: docker compose build)${NC}"
        fi
    fi
}

# Summary
show_summary() {
    echo ""
    echo "=============================================="
    echo "Summary:"
    echo "=============================================="
    
    if [ $ERRORS -gt 0 ]; then
        echo -e "${RED}❌ $ERRORS ERRORS found - MUST fix before deploying${NC}"
    fi
    
    if [ $WARNINGS -gt 0 ]; then
        echo -e "${YELLOW}⚠️  $WARNINGS WARNINGS found - Review recommended${NC}"
    fi
    
    if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}✅ All checks passed! Ready to deploy.${NC}"
        echo ""
        echo "Deployment steps:"
        echo "1. ssh root@46.250.244.245"
        echo "2. cd ~/Nexora001"
        echo "3. ./deploy.sh"
    elif [ $ERRORS -eq 0 ]; then
        echo ""
        echo -e "${YELLOW}⚠️  You can deploy but should review warnings first${NC}"
    else
        echo ""
        echo -e "${RED}❌ Fix errors before deploying to production${NC}"
    fi
}

# Run all checks
check_env_file
check_git_status
check_required_files
check_deploy_script
check_docker
show_summary

exit $ERRORS
