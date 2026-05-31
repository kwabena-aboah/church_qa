web: gunicorn church_qa.wsgi:application --bind 0.0.0.0:$PORT --workers 2
worker: celery -A church_qa worker --loglevel=info
