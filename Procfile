release: npm install && npm run build:css && python manage.py collectstatic --noinput
web: daphne -b 0.0.0.0 -p $PORT sportclub.asgi:application