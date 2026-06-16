# SSL Certificate Setup Guide for Nexora001

## 🎯 Purpose
This guide explains how to generate and install SSL certificates to enable HTTPS on your production server.

---

## 📋 Prerequisites

Before starting, ensure:
- [x] Domain `elanka.ai` points to your server IP `46.250.244.245`
- [x] Port 80 is open and accessible from the internet
- [x] Port 443 is open and accessible from the internet
- [x] Docker containers are running
- [x] You have SSH access to the server

---

## 🚀 Step-by-Step Instructions

### Step 1: Connect to Your Server
```bash
# From your local machine
ssh your_username@46.250.244.245
```

### Step 2: Stop Nginx Container (Temporarily)
```bash
# Navigate to your docker directory
cd /path/to/your/docker-compose-directory

# Stop nginx to free port 80 for certbot
docker-compose stop nginx
```

**Why?** Certbot needs to bind to port 80 to verify domain ownership. Nginx is currently using port 80.

### Step 3: Install Certbot
```bash
# For Ubuntu/Debian
sudo apt update
sudo apt install certbot -y

# For CentOS/RHEL
sudo yum install certbot -y
```

**What is Certbot?** A free tool by Let's Encrypt to automatically generate SSL certificates.

### Step 4: Generate SSL Certificates
```bash
sudo certbot certonly --standalone \
  -d elanka.ai \
  -d www.elanka.ai \
  --email your-email@example.com \
  --agree-tos \
  --non-interactive
```

**What happens here:**
1. Certbot starts a temporary web server on port 80
2. Let's Encrypt verifies you control `elanka.ai` by accessing `http://elanka.ai/.well-known/...`
3. If successful, certificates are generated at `/etc/letsencrypt/live/elanka.ai/`

**Expected Output:**
```
Successfully received certificate.
Certificate is saved at: /etc/letsencrypt/live/elanka.ai/fullchain.pem
Key is saved at:         /etc/letsencrypt/live/elanka.ai/privkey.pem
```

### Step 5: Copy Certificates to Docker Volume
```bash
# Find your docker nginx ssl directory (adjust path as needed)
# This should match the volume mount in docker-compose.yml

# Copy certificates
sudo cp /etc/letsencrypt/live/elanka.ai/fullchain.pem /path/to/Nexora001/nginx/ssl/
sudo cp /etc/letsencrypt/live/elanka.ai/privkey.pem /path/to/Nexora001/nginx/ssl/

# Set proper permissions
sudo chmod 644 /path/to/Nexora001/nginx/ssl/fullchain.pem
sudo chmod 600 /path/to/Nexora001/nginx/ssl/privkey.pem
```

**Why copy?** Docker nginx container reads certificates from the mounted volume, not from `/etc/letsencrypt/`.

### Step 6: Verify Certificates Exist
```bash
ls -lh /path/to/Nexora001/nginx/ssl/
# You should see:
# fullchain.pem
# privkey.pem
```

### Step 7: Enable HTTPS in Nginx Config
```bash
# Edit nginx/default.conf
nano /path/to/Nexora001/nginx/default.conf

# Uncomment the entire HTTPS server block (starts with "# server {" around line 110)
# Also modify the HTTP server to redirect to HTTPS:
# Replace all location blocks in HTTP server with:
#     return 301 https://$server_name$request_uri;
```

**What this does:**
- Enables HTTPS on port 443
- Redirects all HTTP traffic to HTTPS

### Step 8: Restart Nginx
```bash
# Start nginx with new configuration
docker-compose up -d nginx

# Check if nginx started successfully
docker ps | grep nginx
docker logs nexora-nginx --tail 20
```

**Expected:** nginx container should be "Up" with ports `0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp`

### Step 9: Test Your Site
```bash
# Test HTTP (should redirect to HTTPS)
curl -I http://elanka.ai

# Test HTTPS
curl -I https://elanka.ai
```

**Expected:**
- HTTP returns `301 Moved Permanently` with `Location: https://elanka.ai/`
- HTTPS returns `200 OK`

### Step 10: Access Your Site
Open browser: `https://elanka.ai/login`

**Expected:** 
- ✅ Padlock icon in address bar
- ✅ Login page loads
- ✅ Login works (no "Failed to fetch" error)

---

## 🔄 Certificate Auto-Renewal

Let's Encrypt certificates expire every 90 days. Set up auto-renewal:

```bash
# Test renewal (dry run)
sudo certbot renew --dry-run

# If successful, add cron job
sudo crontab -e

# Add this line to run renewal check twice daily:
0 0,12 * * * certbot renew --quiet --post-hook "cp /etc/letsencrypt/live/elanka.ai/*.pem /path/to/Nexora001/nginx/ssl/ && docker-compose -f /path/to/docker-compose.yml restart nginx"
```

**What this does:** Checks for expiring certificates twice a day and renews them automatically.

---

## 🔧 Troubleshooting

### Issue: Certbot fails with "Port 80 already in use"
**Solution:** 
```bash
docker-compose stop nginx
# Try certbot again
```

### Issue: "Failed to connect to the ACME server"
**Solution:** Check firewall
```bash
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### Issue: Nginx fails to start after enabling HTTPS
**Solution:** Check logs
```bash
docker logs nexora-nginx
# Common issue: Certificate files not found
# Verify: ls /path/to/Nexora001/nginx/ssl/
```

### Issue: Site works but shows "Not Secure"
**Solution:** Check if you're accessing via IP instead of domain
- ❌ `https://46.250.244.245` (IP - no certificate)
- ✅ `https://elanka.ai` (Domain - has certificate)

---

## 📝 Summary

**What you did:**
1. Generated free SSL certificates using Let's Encrypt
2. Copied certificates to Docker nginx volume
3. Enabled HTTPS in nginx configuration
4. Set up automatic certificate renewal

**Result:**
- ✅ Your site is now secured with HTTPS
- ✅ Browser shows padlock icon
- ✅ No more "Failed to fetch" errors
- ✅ Certificates auto-renew every 90 days

---

## 🆘 Need Help?

If you encounter issues:
1. Check nginx logs: `docker logs nexora-nginx --tail 50`
2. Check certificate files: `ls -lh /path/to/Nexora001/nginx/ssl/`
3. Test nginx config: `docker exec nexora-nginx nginx -t`
4. Verify domain DNS: `nslookup elanka.ai`
