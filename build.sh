#!/usr/bin/env bash
set -e

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Creating static directory..."
mkdir -p "$(dirname "$0")/static/css"

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Build complete"
