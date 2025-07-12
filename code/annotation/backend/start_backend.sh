#!/bin/bash

echo "Environment: $ENV"
echo "Allowed origins: $ALLOWED_ORIGINS"

if [ "$ENV" = "production" ]; then
  echo "Starting Flask backend with gunicorn on port $PORT..."
  exec gunicorn app:app --bind 0.0.0.0:$PORT --workers 4
else
  echo "Starting Flask backend with Flask development server on port 5001..."
  export FLASK_APP=app.py
  export FLASK_ENV=development
  flask run --host=0.0.0.0 --port=5001
fi
