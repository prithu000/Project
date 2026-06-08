#!/bin/bash

# CamCap AWS EC2 Deployment Script
# Run this on your EC2 instance after initial setup

echo "🚀 CamCap Deployment Script for AWS EC2"
echo "========================================"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as ubuntu user
if [ "$USER" != "ubuntu" ]; then
    echo -e "${RED}❌ Please run as ubuntu user${NC}"
    exit 1
fi

# Set project directory
PROJECT_DIR="/home/ubuntu/camcap"
cd $PROJECT_DIR

echo -e "${BLUE}📦 Pulling latest code from GitHub...${NC}"
git pull origin main

echo -e "${BLUE}🐍 Activating virtual environment...${NC}"
source venv/bin/activate

echo -e "${BLUE}📥 Installing/updating Python packages...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

echo -e "${BLUE}🗄️  Running database migrations...${NC}"
python manage.py migrate --noinput

echo -e "${BLUE}📁 Collecting static files...${NC}"
python manage.py collectstatic --noinput --clear

echo -e "${BLUE}🧹 Cleaning old converted files (7+ days)...${NC}"
find media/converted -name "*.mp4" -mtime +7 -delete 2>/dev/null || true

echo -e "${BLUE}🔄 Restarting Gunicorn...${NC}"
sudo systemctl restart gunicorn

echo -e "${BLUE}🔄 Restarting Nginx...${NC}"
sudo systemctl restart nginx

echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo "Service Status:"
sudo systemctl status gunicorn --no-pager -l
echo ""
sudo systemctl status nginx --no-pager -l
echo ""
echo -e "${GREEN}🎉 CamCap is now live!${NC}"
