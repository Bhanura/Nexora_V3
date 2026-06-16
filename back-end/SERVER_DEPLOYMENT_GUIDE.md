# 🚀 SERVER DEPLOYMENT GUIDE - Nexora001 Docker Migration

Complete step-by-step guide to migrate your Nexora001 application from SystemD/nginx to Docker on your Contabo server.

**Server**: 46.250.244.245  
**OS**: Ubuntu 24.04.3 LTS

---

## 📋 PHASE 1: BACKUP & PREPARATION

### Step 1.1: SSH to Server
```bash
ssh root@46.250.244.245
```

### Step 1.2: Backup Current Data
```bash
# Create backup directory
mkdir -p ~/backups/$(date +%Y%m%d)
cd ~/backups/$(date +%Y%m%d)

# Backup MongoDB Atlas data (if you have mongodump access)
# Get connection string from your current .env
mongodump --uri="your-mongodb-atlas-uri" --out=./mongodb_backup

# Or export specific database
mongodump --uri="your-mongodb-atlas-uri" --db=nexora001 --out=./mongodb_backup

# Backup current code
tar -czf code_backup.tar.gz ~/Nexora001 ~/Nexora001_Frontend

# Backup current SystemD service
cp /etc/systemd/system/nexora*.service . 2>/dev/null || echo "No systemd service found"

# Backup nginx config
cp /etc/nginx/sites-available/* . 2>/dev/null || echo "No nginx config found"

echo "✅ Backup completed in $(pwd)"
```

### Step 1.3: Stop Current Services
```bash
# Stop SystemD service (check actual service name first)
systemctl list-units --type=service | grep nexora
systemctl stop nexora001.service  # Adjust name if different
systemctl disable nexora001.service

# Stop nginx
systemctl stop nginx
systemctl disable nginx

# Verify nothing is running
netstat -tulpn | grep -E ':(80|8000|443)'
```

### Step 1.4: Install Docker (if not installed)
```bash
# Check if Docker is installed
docker --version

# If not installed:
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install docker-compose
apt-get update
apt-get install -y docker-compose-plugin

# Verify installation
docker --version
docker compose version

# Enable Docker service
systemctl enable docker
systemctl start docker
```

---

## 📂 PHASE 2: UPDATE CODE

### Step 2.1: Update Backend Repository
```bash
cd ~/Nexora001

# Stash any local changes
git stash

# Pull latest code (with Docker files)
git pull origin main

# Or if you pushed to a different branch
git fetch origin
git checkout docker-migration  # or your branch name
git pull origin docker-migration
```

### Step 2.2: Update Frontend Repository
```bash
cd ~/Nexora001_Frontend

# Pull latest code (with Dockerfile)
git stash
git pull origin main
```

### Step 2.3: Verify Docker Files Exist
```bash
cd ~/Nexora001

# Check files
ls -la Dockerfile docker-compose.yml
ls -la nginx/default.conf
ls -la ../Nexora001_Frontend/Dockerfile
ls -la ../Nexora001_Frontend/nginx.conf

echo "✅ All Docker files present"
```

---

## 🔐 PHASE 3: CONFIGURE ENVIRONMENT

### Step 3.1: Create Production .env File
```bash
cd ~/Nexora001

# Copy example
cp .env.example .env

# Edit with secure values
nano .env
```

### Step 3.2: Set Production Values in .env
```env
# MongoDB (Docker local instance)
MONGO_ROOT_USER=admin
MONGO_ROOT_PASSWORD=CHANGE_THIS_TO_STRONG_PASSWORD
MONGODB_URI=mongodb://admin:CHANGE_THIS_TO_STRONG_PASSWORD@mongodb:27017
MONGODB_DATABASE=nexora001

# Qdrant
USE_QDRANT=true
QDRANT_URL=http://qdrant:6333

# Google API Key (your actual key)
GOOGLE_API_KEY=your-real-google-api-key

# JWT Secret (generate secure key)
JWT_SECRET_KEY=$(openssl rand -hex 32)

# Production settings
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
```

**💡 TIP**: Generate secure password: `openssl rand -base64 32`

### Step 3.3: Secure .env File
```bash
chmod 600 .env
chown root:root .env
```

---

## 🏗️ PHASE 4: BUILD & DEPLOY CONTAINERS

### Step 4.1: Build All Images
```bash
cd ~/Nexora001

# Build all services
docker compose build --no-cache

# This will take 5-10 minutes
# Watch for any errors in output
```

### Step 4.2: Start All Services
```bash
# Start in detached mode
docker compose up -d

# Wait for containers to start
sleep 30

# Check status
docker compose ps
```

**Expected Output:**
```
NAME                IMAGE                  STATUS
nexora-mongodb      mongo:8.0              Up (healthy)
nexora-qdrant       qdrant/qdrant:latest   Up (healthy)
nexora-backend      nexora001-backend      Up (healthy)
nexora-frontend     nexora001-frontend     Up (healthy)
nexora-nginx        nginx:alpine           Up (healthy)
```

### Step 4.3: Check Logs
```bash
# View all logs
docker compose logs -f

# Or check specific services
docker compose logs backend
docker compose logs qdrant
docker compose logs nginx
```

---

## 🔄 PHASE 5: DATA MIGRATION

### Step 5.1: Restore MongoDB Data
```bash
# Copy backup to container
cd ~/backups/$(date +%Y%m%d)

# Restore to local MongoDB
docker exec -i nexora-mongodb mongorestore \
  --username=admin \
  --password=YOUR_PASSWORD \
  --authenticationDatabase=admin \
  --db=nexora001 \
  --dir=/tmp/mongodb_backup/nexora001

# Or import from stdin
tar -xzf mongodb_backup.tar.gz
docker cp mongodb_backup nexora-mongodb:/tmp/
docker exec nexora-mongodb mongorestore \
  --username=admin \
  --password=YOUR_PASSWORD \
  --authenticationDatabase=admin \
  /tmp/mongodb_backup
```

### Step 5.2: Verify Data Import
```bash
# Connect to MongoDB
docker exec -it nexora-mongodb mongosh -u admin -p YOUR_PASSWORD

# Check data
use nexora001
db.documents.count()
db.users.count()
show collections
exit
```

### Step 5.3: Re-generate Embeddings for Qdrant
```bash
# If you need to regenerate embeddings, use the backend API
# This will be done through the ingestion endpoints

# Or run a migration script
docker exec -it nexora-backend python migrate_to_selfhosted.py
```

---

## ✅ PHASE 6: VERIFY DEPLOYMENT

### Step 6.1: Test Internal Services
```bash
# Test MongoDB
docker exec nexora-mongodb mongosh -u admin -p YOUR_PASSWORD --eval "db.adminCommand('ping')"

# Test Qdrant
curl http://localhost:6333
curl http://localhost:6333/collections

# Test Backend (internal)
docker exec nexora-backend curl http://localhost:8000/
```

### Step 6.2: Test External Access
```bash
# Test nginx health
curl http://localhost/health

# Test API
curl http://46.250.244.245/api/
curl http://46.250.244.245/api/docs

# Test frontend
curl -I http://46.250.244.245/

# Open in browser
echo "Visit: http://46.250.244.245"
```

### Step 6.3: Test Full Flow
1. Open browser: `http://46.250.244.245`
2. Register a new user
3. Login
4. Upload a test document
5. Try RAG chat query
6. Check Qdrant dashboard: `http://46.250.244.245:6333/dashboard`

---

## 🔒 PHASE 7: SECURITY & SSL (Optional but Recommended)

### Step 7.1: Install Certbot in Nginx Container
```bash
# Update nginx service in docker-compose.yml to include certbot
# Or use reverse proxy with Let's Encrypt

# Simple approach: Use certbot standalone
apt-get install -y certbot

# Stop nginx container temporarily
docker compose stop nginx

# Get certificate
certbot certonly --standalone -d your-domain.com

# Copy certificates to nginx volume
mkdir -p ~/Nexora001/nginx/ssl
cp /etc/letsencrypt/live/your-domain.com/* ~/Nexora001/nginx/ssl/

# Update nginx config for HTTPS (already in default.conf)
# Uncomment HTTPS server block in nginx/default.conf

# Restart nginx
docker compose up -d nginx
```

### Step 7.2: Update Firewall
```bash
# Allow HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Remove old backend port if exposed
# (not needed with reverse proxy)
```

---

## 🎛️ PHASE 8: MONITORING & MAINTENANCE

### Step 8.1: Setup Auto-restart
```bash
# Containers already configured with restart: always
# Verify with:
docker compose ps
```

### Step 8.2: Monitor Resources
```bash
# Real-time stats
docker stats

# Disk usage
docker system df

# Container health
docker compose ps
```

### Step 8.3: Setup Log Rotation
```bash
# Configure Docker log rotation
cat > /etc/docker/daemon.json << EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

# Restart Docker
systemctl restart docker

# Restart containers
cd ~/Nexora001
docker compose restart
```

### Step 8.4: Create Deployment Script
```bash
# The deploy.sh script should already exist
chmod +x deploy.sh

# Test it
./deploy.sh
```

---

## 🧹 PHASE 9: CLEANUP (After 48h of Stable Operation)

### Step 9.1: Remove Old Services
```bash
# Remove SystemD service files
rm /etc/systemd/system/nexora*.service
systemctl daemon-reload

# Remove old nginx config
rm /etc/nginx/sites-enabled/nexora*
rm /etc/nginx/sites-available/nexora*

# Uninstall nginx (now using container)
apt-get remove -y nginx nginx-common
apt-get autoremove -y
```

### Step 9.2: Clean Old Python Environment
```bash
# Remove old virtual environment (if any)
rm -rf ~/Nexora001/venv

# Remove old dependencies
apt-get remove -y python3-pip
apt-get autoremove -y
```

---

## 🔄 ONGOING OPERATIONS

### Update Deployment
```bash
cd ~/Nexora001
./deploy.sh
```

### View Logs
```bash
# Real-time logs
docker compose logs -f

# Last 100 lines
docker compose logs --tail=100

# Specific service
docker compose logs -f backend
```

### Restart Services
```bash
# Restart all
docker compose restart

# Restart specific service
docker compose restart backend
```

### Backup Database
```bash
# MongoDB backup
docker exec nexora-mongodb mongodump \
  --username=admin \
  --password=YOUR_PASSWORD \
  --authenticationDatabase=admin \
  --out=/tmp/backup

# Copy backup out
docker cp nexora-mongodb:/tmp/backup ./mongodb_backup_$(date +%Y%m%d)

# Qdrant backup (automatic via volume)
# Volume: qdrant_storage
docker run --rm -v nexora001_qdrant_storage:/data -v $(pwd):/backup \
  alpine tar czf /backup/qdrant_backup_$(date +%Y%m%d).tar.gz /data
```

---

## 🆘 TROUBLESHOOTING

### Issue: Containers won't start
```bash
# Check logs
docker compose logs

# Check individual container
docker logs nexora-backend

# Check Docker daemon
systemctl status docker
```

### Issue: Can't access from internet
```bash
# Check firewall
ufw status

# Check nginx is listening
docker compose ps nginx
docker exec nexora-nginx netstat -tulpn

# Check from outside
curl -I http://46.250.244.245
```

### Issue: Backend can't connect to MongoDB
```bash
# Check network
docker network ls
docker network inspect nexora001_nexora-network

# Test connectivity
docker exec nexora-backend ping mongodb
docker exec nexora-backend curl http://mongodb:27017
```

### Issue: Out of disk space
```bash
# Check usage
df -h
docker system df

# Clean up
docker system prune -a
docker volume prune
```

---

## 📊 MIGRATION CHECKLIST

- [ ] Backed up MongoDB Atlas data
- [ ] Backed up current code and configs
- [ ] Stopped old SystemD service
- [ ] Stopped old nginx
- [ ] Docker and docker-compose installed
- [ ] Updated Git repositories
- [ ] Created production .env file
- [ ] Built all Docker images
- [ ] Started all containers (5 healthy)
- [ ] Restored MongoDB data
- [ ] Verified Qdrant collections
- [ ] Tested API endpoints
- [ ] Tested frontend
- [ ] Tested full user flow
- [ ] Setup SSL (optional)
- [ ] Configured firewall
- [ ] Monitored for 24-48 hours
- [ ] Cleaned up old services

---

## 🎯 SUCCESS CRITERIA

✅ All 5 containers running and healthy  
✅ API accessible at http://46.250.244.245/api/docs  
✅ Frontend accessible at http://46.250.244.245  
✅ Users can login and use the system  
✅ RAG queries work with Qdrant  
✅ No errors in logs  
✅ System stable for 48+ hours  

---

**🎉 Congratulations!** Your Nexora001 is now running in Docker with self-hosted Qdrant vector search!

**Need Help?** Check logs: `docker compose logs -f`
