#!/usr/bin/env bash
# Render build script for Cam Cap

set -o errexit

# Install FFmpeg
apt-get update && apt-get install -y ffmpeg

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate --no-input
