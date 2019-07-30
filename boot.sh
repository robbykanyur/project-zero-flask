#!/bin/sh
source venv/bin/activate
exec gunicorn -b :5000 --chdir src --log-level=warning wsgi:app
