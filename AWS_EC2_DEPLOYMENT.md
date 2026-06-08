# AWS EC2 Deployment Guide for CamCap

## ✅ Pre-Deployment Checklist

Your website is **READY** for AWS EC2 deployment! Here's what we have:

### ✅ Configuration Files
- ✅ `requirements.txt` - All Python dependencies
- ✅ `.env.example` - Environment variables template
- ✅ `settings.py` - Production-ready with environment detection
- ✅ `runtime.txt` - Python version specified
- ✅ Database support - PostgreSQL (production) + SQLite (development)
- ✅ Static files - WhiteNoise for serving
- ✅ Security - Environment-based SECRET_KEY, CSRF, ALLOWED_HOSTS

### ✅ Features Working
- ✅ Google OAuth login
- ✅ Razorpay payment gateway
- ✅ Order management & tracking
- ✅ Email notifications
- ✅ File converter (.build to MP4)
- ✅ Pincode-based address auto-fill

---

## 🚀 AWS EC2 Deployment Steps

### Step 1: Launch EC2 Instance

1. **Go to AWS Console** → EC2 → Launch Instance
2. **Choose AMI**: Ubuntu Server 22.04 LTS (Free tier eligible)
3. **Instance Type**: t2.micro (1GB RAM, 1 vCPU) - Free tier
4. **Key Pair**: Create new or use existing .pem file
5. **Security Group Rules**:
   - SSH (22) - Your IP
   - HTTP (80) - 0.0.0.0/0
   - HTTPS (443) - 0.0.0.0/0
   - Custom TCP (8000) - 0.0.0.0/0 (for testing)
6. **Storage**: 15-20 GB (enough for files + videos)
7. **Launch Instance**

### Step 2: Connect to EC2

```bash
# Make key file secure
chmod 400 your-key.pem

# Connect to EC2
ssh -i "your-key.pem" ubuntu@your-ec2-public-ip
```

### Step 3: Update & Install Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11+, pip, and venv
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install PostgreSQL (recommended for production)
sudo apt install postgresql postgresql-contrib -y

# Install Nginx (web server)
sudo apt install nginx -y

# Install Git
sudo apt install git -y

# Install system dependencies for Pillow
sudo apt install python3-dev libjpeg-dev zlib1g-dev -y
```

### Step 4: Setup PostgreSQL Database

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE camcap_db;
CREATE USER camcap_user WITH PASSWORD 'your_strong_password_here';
ALTER ROLE camcap_user SET client_encoding TO 'utf8';
ALTER ROLE camcap_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE camcap_user SET timezone TO 'Asia/Kolkata';
GRANT ALL PRIVILEGES ON DATABASE camcap_db TO camcap_user;
\q
```

### Step 5: Clone & Setup Project

```bash
# Navigate to home directory
cd /home/ubuntu

# Clone repository
git clone https://github.com/prithu000/Project.git camcap
cd camcap

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install requirements
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 6: Configure Environment Variables

```bash
# Create .env file
nano .env
```

**Add these variables:**
```env
# Django Configuration
DJANGO_SECRET_KEY=generate-a-new-random-secret-key-here-50-chars
ENVIRONMENT=production
DEBUG=False

# Database (PostgreSQL)
DATABASE_URL=postgresql://camcap_user:your_strong_password_here@localhost:5432/camcap_db

# Allowed Hosts (replace with your actual domain/IP)
ALLOWED_HOSTS=your-domain.com,your-ec2-ip,www.your-domain.com
CSRF_TRUSTED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Email Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=YOUR_GMAIL_APP_PASSWORD_HERE

# Google OAuth
GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID_HERE.apps.googleusercontent.com
GOOGLE_SECRET=YOUR_GOOGLE_SECRET_KEY_HERE

# Razorpay (switch to LIVE keys for production)
RAZORPAY_KEY_ID=YOUR_RAZORPAY_TEST_KEY_ID_HERE
RAZORPAY_KEY_SECRET=YOUR_RAZORPAY_TEST_SECRET_HERE
```

**Save and exit**: `Ctrl+O`, `Enter`, `Ctrl+X`

### Step 7: Run Django Setup

```bash
# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create superuser for admin
python manage.py createsuperuser
# Username: admin
# Email: your-email@gmail.com
# Password: (choose a strong password)

# Test if server runs
python manage.py runserver 0.0.0.0:8000
```

**Test in browser**: `http://your-ec2-ip:8000`

### Step 8: Setup Gunicorn (Production WSGI Server)

```bash
# Test Gunicorn
gunicorn --bind 0.0.0.0:8000 camcap.wsgi:application
```

**Create systemd service:**
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

**Add this content:**
```ini
[Unit]
Description=gunicorn daemon for CamCap
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/camcap
Environment="PATH=/home/ubuntu/camcap/venv/bin"
ExecStart=/home/ubuntu/camcap/venv/bin/gunicorn \
          --workers 3 \
          --bind unix:/home/ubuntu/camcap/camcap.sock \
          --timeout 300 \
          camcap.wsgi:application

[Install]
WantedBy=multi-user.target
```

**Enable and start Gunicorn:**
```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
sudo systemctl status gunicorn
```

### Step 9: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/camcap
```

**Add this configuration:**
```nginx
server {
    listen 80;
    server_name your-ec2-ip your-domain.com www.your-domain.com;
    
    client_max_body_size 2G;  # For large video uploads
    
    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /home/ubuntu/camcap/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /home/ubuntu/camcap/media/;
        expires 30d;
    }
    
    location / {
        include proxy_params;
        proxy_pass http://unix:/home/ubuntu/camcap/camcap.sock;
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }
}
```

**Enable site and restart Nginx:**
```bash
sudo ln -s /etc/nginx/sites-available/camcap /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 10: Setup SSL (HTTPS) with Let's Encrypt

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal is configured by certbot
sudo certbot renew --dry-run
```

---

## 🔧 Post-Deployment Configuration

### 1. Update Google OAuth Redirect URIs
Go to Google Cloud Console → Credentials → Your OAuth Client:
- Add: `https://your-domain.com/accounts/google/login/callback/`
- Add: `http://your-ec2-ip:8000/accounts/google/login/callback/` (for testing)

### 2. Switch Razorpay to Live Mode
When ready for production:
- Login to Razorpay Dashboard
- Get LIVE API keys
- Update `.env` with live keys

### 3. Setup Database Backups
```bash
# Create backup script
nano ~/backup_db.sh
```

**Add:**
```bash
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
sudo -u postgres pg_dump camcap_db > $BACKUP_DIR/camcap_db_$DATE.sql
# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
```

**Make executable and schedule:**
```bash
chmod +x ~/backup_db.sh
crontab -e
# Add: 0 2 * * * /home/ubuntu/backup_db.sh
```

### 4. Setup Media File Cleanup
```bash
# Clean old converted files (older than 7 days)
crontab -e
# Add: 0 3 * * * find /home/ubuntu/camcap/media/converted -name "*.mp4" -mtime +7 -delete
```

---

## 📊 Monitoring & Maintenance

### Check Service Status
```bash
# Gunicorn status
sudo systemctl status gunicorn

# Nginx status
sudo systemctl status nginx

# View Gunicorn logs
sudo journalctl -u gunicorn -f

# View Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

### Restart Services After Code Updates
```bash
cd /home/ubuntu/camcap
source venv/bin/activate
git pull origin main
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
sudo systemctl restart nginx
```

### Django Admin Access
- URL: `https://your-domain.com/admin/`
- Username: admin
- Password: (what you set during createsuperuser)

---

## 🔒 Security Checklist

- ✅ SSH key-based authentication (disable password login)
- ✅ Security groups configured (only necessary ports open)
- ✅ SSL certificate installed (HTTPS)
- ✅ DEBUG=False in production
- ✅ Strong SECRET_KEY (50+ random characters)
- ✅ Database password protected
- ✅ .env file secured (chmod 600)
- ✅ Regular security updates: `sudo apt update && sudo apt upgrade`
- ✅ Firewall enabled: `sudo ufw enable`

---

## 💰 Cost Estimation (AWS Free Tier)

- **EC2 t2.micro**: Free for 12 months (750 hours/month)
- **Storage (20GB EBS)**: Free for 12 months (30GB/month)
- **Data Transfer**: 15GB out/month free
- **After free tier**: ~$8-10/month for t2.micro

**Optimization Tips:**
- Use CloudFront CDN for static files (free tier: 50GB out/month)
- Consider S3 for media storage (free tier: 5GB storage)
- Setup auto-scaling if traffic increases

---

## 🆘 Common Issues & Solutions

### Issue: Static files not loading
```bash
python manage.py collectstatic --noinput
sudo systemctl restart gunicorn
```

### Issue: 502 Bad Gateway
```bash
# Check Gunicorn is running
sudo systemctl status gunicorn
# Check socket file exists
ls -l /home/ubuntu/camcap/camcap.sock
```

### Issue: Database connection error
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql
# Verify DATABASE_URL in .env
```

### Issue: Permission denied
```bash
# Fix permissions
sudo chown -R ubuntu:www-data /home/ubuntu/camcap
sudo chmod -R 755 /home/ubuntu/camcap
```

---

## 📞 Support & Resources

- **GitHub Repo**: https://github.com/prithu000/Project.git
- **AWS EC2 Documentation**: https://docs.aws.amazon.com/ec2/
- **Django Deployment**: https://docs.djangoproject.com/en/5.0/howto/deployment/
- **Gunicorn**: https://docs.gunicorn.org/
- **Nginx**: https://nginx.org/en/docs/

---

## ✅ Your Website is Production-Ready!

All configurations are in place:
- ✅ Environment-based settings
- ✅ Database configuration (SQLite + PostgreSQL support)
- ✅ Static files with WhiteNoise
- ✅ Security headers
- ✅ Email notifications
- ✅ Payment gateway
- ✅ OAuth authentication

**Next Steps**: Follow the deployment steps above to go live on AWS EC2! 🚀
