# 🌐 Production Configuration Guide

## Overview

This guide explains how the system handles localhost vs production URLs and what needs to be configured when deploying to a server.

---

## ✅ What's Already Working (No Changes Needed)

### 1. **Frontend API Calls** ✅
**File**: `Nexora001_Frontend/src/config.js`
```javascript
export const API_BASE_URL = import.meta.env.VITE_API_URL || 
  (import.meta.env.PROD ? "/api" : "http://localhost:8000/api");
```

**How it works:**
- **Development**: Uses `http://localhost:8000/api`
- **Production (Docker)**: Uses `/api` (relative path, proxied by nginx)
- Automatically detects environment
- **✅ No configuration needed**

### 2. **Widget Embed Instructions** ✅
**File**: `Nexora001_Frontend/src/components/features/WidgetEmbedPanel.jsx`
```javascript
const embedCodeCDN = async () => {
  return `<script>
    script.src = '${window.location.origin}/widget.iife.js';
    window.NexoraWidget.init('${apiKey}', {
      apiUrl: '${window.location.origin}/api'
    });
  </script>`;
};
```

**How it works:**
- Uses `window.location.origin` - **dynamically detects the current URL**
- **On localhost**: Shows `http://localhost/widget.iife.js` and `http://localhost/api`
- **On server**: Shows `http://46.250.244.245/widget.iife.js` and `http://46.250.244.245/api`
- **With domain**: Shows `https://yourdomain.com/widget.iife.js` and `https://yourdomain.com/api`
- **✅ No configuration needed** - automatically adapts to current domain

### 3. **Internal Docker Networking** ✅
**File**: `.env` (for internal container communication)
```env
MONGODB_URI=mongodb://admin:password@mongodb:27017
QDRANT_URL=http://qdrant:6333
```

**How it works:**
- Container names (`mongodb`, `qdrant`, `backend`, `frontend`) are used for **internal** communication
- These are Docker network names, not public URLs
- **✅ No changes needed** - same for localhost and server

### 4. **Nginx Reverse Proxy** ✅
**File**: `nginx/default.conf`
```nginx
location /api/ {
    proxy_pass http://backend/api/;
}
```

**How it works:**
- Nginx routes external `/api/*` requests to internal `backend:8000`
- Works on any domain/IP
- **✅ No configuration needed**

---

## 🔧 What Needs Configuration on Server

### 1. **Environment Variables** (`.env` file)

**On Server**: Create/update `~/Nexora001/.env`

```bash
ssh root@46.250.244.245
cd ~/Nexora001
nano .env
```

**Required Changes for Production:**

```env
# =============================================================================
# SECURITY - MUST CHANGE FOR PRODUCTION
# =============================================================================
MONGO_ROOT_PASSWORD=<GENERATE_STRONG_PASSWORD>  # Use: openssl rand -base64 32
JWT_SECRET_KEY=<GENERATE_STRONG_SECRET>         # Use: openssl rand -hex 32

# MongoDB connection (use strong password from above)
MONGODB_URI=mongodb://admin:<SAME_STRONG_PASSWORD>@mongodb:27017
MONGODB_DATABASE=nexora001

# =============================================================================
# GOOGLE API KEY - REQUIRED
# =============================================================================
GOOGLE_API_KEY=<YOUR_ACTUAL_GOOGLE_API_KEY>

# =============================================================================
# PRODUCTION SETTINGS
# =============================================================================
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# =============================================================================
# SERVICES - KEEP AS IS (Docker internal names)
# =============================================================================
QDRANT_URL=http://qdrant:6333
USE_QDRANT=true

# =============================================================================
# EMAIL (Optional - for notifications)
# =============================================================================
SMTP_ENABLED=false  # Change to true if you want email notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password
SENDER_EMAIL=your-email@gmail.com
```

**Security Commands:**
```bash
# Generate strong MongoDB password
openssl rand -base64 32

# Generate JWT secret
openssl rand -hex 32

# Secure .env file
chmod 600 .env
chown root:root .env
```

### 2. **Firewall Configuration**

```bash
# Allow HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw enable

# Check status
ufw status
```

### 3. **SSL Certificate (Optional but Recommended)**

**Option A: Let's Encrypt (Free)**
```bash
# Install certbot
apt-get update
apt-get install -y certbot

# Stop nginx temporarily
docker compose stop nginx

# Get certificate (replace with your domain)
certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# Copy certificates
mkdir -p ~/Nexora001/nginx/ssl
cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ~/Nexora001/nginx/ssl/
cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ~/Nexora001/nginx/ssl/

# Update nginx config (uncomment HTTPS block in nginx/default.conf)
cd ~/Nexora001
nano nginx/default.conf  # Uncomment lines 52-92

# Restart nginx
docker compose up -d nginx
```

**Option B: Cloudflare (Free SSL + CDN)**
1. Add your domain to Cloudflare
2. Update DNS to point to `46.250.244.245`
3. Enable SSL in Cloudflare dashboard
4. No nginx changes needed - Cloudflare handles SSL

---

## 🧪 Testing Production Deployment

### 1. **Test Internal Services**
```bash
# SSH to server
ssh root@46.250.244.245

# Test MongoDB
docker exec nexora-mongodb mongosh -u admin -p YOUR_PASSWORD --eval "db.adminCommand('ping')"

# Test Qdrant
curl http://localhost:6333
curl http://localhost:6333/collections

# Test Backend
curl http://localhost:8000/api/
curl http://localhost:8000/api/docs
```

### 2. **Test External Access**
```bash
# From your local machine
curl http://46.250.244.245/api/
curl http://46.250.244.245/
```

### 3. **Test in Browser**
1. Visit: `http://46.250.244.245`
2. Register/Login
3. Check browser console - should see API calls to `http://46.250.244.245/api/...`
4. Go to Widget Settings
5. Copy embed code - should show `http://46.250.244.245/api`
6. Test widget on external website

---

## 📱 Widget Embedding on External Sites

### For Customers Using Your Widget:

**Option 1: CDN-hosted (Recommended)**
```html
<script>
  (function() {
    var script = document.createElement('script');
    script.src = 'http://46.250.244.245/widget.iife.js';  <!-- Your server URL -->
    script.onload = function() {
      window.NexoraWidget.init('nx_customer_api_key_here', {
        apiUrl: 'http://46.250.244.245/api'  <!-- Your server URL -->
      });
    };
    document.body.appendChild(script);
  })();
</script>
```

**With Custom Domain:**
```html
<script>
  (function() {
    var script = document.createElement('script');
    script.src = 'https://chat.yourdomain.com/widget.iife.js';
    script.onload = function() {
      window.NexoraWidget.init('nx_customer_api_key_here', {
        apiUrl: 'https://chat.yourdomain.com/api'
      });
    };
    document.body.appendChild(script);
  })();
</script>
```

**Important Notes:**
- Customers embed the widget on **their own websites**
- The widget calls **back to your Nexora server** API
- Your server must be publicly accessible
- Use HTTPS in production for security

---

## 🔍 How URLs Are Resolved

### Scenario 1: Local Development
- **User accesses**: `http://localhost/`
- **Frontend sees**: `window.location.origin = "http://localhost"`
- **API calls go to**: `/api/` → nginx proxy → `backend:8000/api/`
- **Widget embed shows**: `http://localhost/widget.iife.js`
- **Widget API calls go to**: `http://localhost/api/`

### Scenario 2: Server with IP
- **User accesses**: `http://46.250.244.245/`
- **Frontend sees**: `window.location.origin = "http://46.250.244.245"`
- **API calls go to**: `/api/` → nginx proxy → `backend:8000/api/`
- **Widget embed shows**: `http://46.250.244.245/widget.iife.js`
- **Widget API calls go to**: `http://46.250.244.245/api/`

### Scenario 3: Server with Custom Domain
- **User accesses**: `https://chat.yourdomain.com/`
- **Frontend sees**: `window.location.origin = "https://chat.yourdomain.com"`
- **API calls go to**: `/api/` → nginx proxy → `backend:8000/api/`
- **Widget embed shows**: `https://chat.yourdomain.com/widget.iife.js`
- **Widget API calls go to**: `https://chat.yourdomain.com/api/`

**✅ Everything is dynamic - no code changes needed!**

---

## 🚨 Common Issues & Solutions

### Issue 1: Widget shows localhost URLs on server
**Symptom**: Embed code shows `http://localhost/widget.iife.js`
**Cause**: Accessing server via SSH tunnel or port forward
**Solution**: Access server directly via IP or domain in browser

### Issue 2: API calls fail with CORS error
**Symptom**: Browser console shows CORS error
**Cause**: Widget on external site can't call your server
**Solution**: 
```python
# Already configured in main.py:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows widget to work on any domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue 3: Can't access server from internet
**Symptom**: Works on server via `curl localhost` but not from outside
**Cause**: Firewall blocking ports
**Solution**:
```bash
# Check firewall
ufw status

# Allow ports
ufw allow 80/tcp
ufw allow 443/tcp

# Check nginx binding
docker exec nexora-nginx netstat -tulpn | grep 80
```

### Issue 4: MongoDB/Qdrant connection failed
**Symptom**: Backend logs show connection errors
**Cause**: Container names not resolving
**Solution**:
```bash
# Check Docker network
docker network inspect nexora001_nexora-network

# Verify services are on same network
docker compose ps
```

---

## 📋 Deployment Checklist

### Pre-deployment:
- [ ] Update `.env` with production values
- [ ] Generate strong passwords (MongoDB, JWT)
- [ ] Obtain real Google API key
- [ ] Commit and push code to GitHub

### Server Setup:
- [ ] Pull latest code: `git pull origin main`
- [ ] Create/update `.env` file
- [ ] Secure `.env`: `chmod 600 .env`
- [ ] Configure firewall (ports 80, 443)
- [ ] (Optional) Setup SSL certificate

### Deployment:
- [ ] Run: `./deploy.sh`
- [ ] Verify all containers healthy: `docker compose ps`
- [ ] Check logs: `docker compose logs -f`
- [ ] Test API: `curl http://YOUR_IP/api/`
- [ ] Test frontend: Open `http://YOUR_IP` in browser

### Verification:
- [ ] Login to dashboard
- [ ] Check API calls go to correct URL (browser console)
- [ ] Upload test document
- [ ] Test RAG query
- [ ] Check widget embed code shows server URL
- [ ] Test widget on external site

### Post-deployment:
- [ ] Monitor logs for 24 hours
- [ ] Set up backups (MongoDB, Qdrant)
- [ ] Configure log rotation
- [ ] (Optional) Setup monitoring (Uptime Robot, etc.)

---

## 🎯 Summary

### ✅ Already Handled Automatically:
1. Frontend API URL detection (development vs production)
2. Widget embed code generation (uses `window.location.origin`)
3. Internal Docker container networking
4. Nginx reverse proxy configuration

### 🔧 Requires Manual Configuration:
1. `.env` file with production values (passwords, API keys)
2. Firewall rules (ports 80, 443)
3. SSL certificate (optional but recommended)
4. Domain DNS configuration (if using custom domain)

### 🎉 Result:
Once properly configured, the system works identically on:
- **Local development**: `http://localhost`
- **Server with IP**: `http://46.250.244.245`
- **Server with domain**: `https://chat.yourdomain.com`

**No code changes needed between environments!** The system automatically detects and adapts to the current URL.
