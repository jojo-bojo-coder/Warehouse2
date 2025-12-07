#!/bin/bash
set -e

echo "=== Building Tailwind CSS ==="
npm install
npm run build:css

# Verify CSS was created
if [ ! -f "./sportclub/static/css/output.css" ]; then
    echo "ERROR: CSS not generated!"
    exit 1
fi

echo "=== Collecting static files ==="
python manage.py collectstatic --noinput --clear

echo "=== Running migrations ==="
python manage.py migrate --noinput

echo "=== Build completed ==="