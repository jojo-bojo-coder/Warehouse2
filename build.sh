#!/bin/bash
# Exit on error
set -e

echo "=== Installing Node dependencies ==="
npm install

echo "=== Building Tailwind CSS ==="
npm run build:css

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput --clear

echo "=== Running migrations ==="
python manage.py migrate --noinput

echo "=== Build completed successfully ==="