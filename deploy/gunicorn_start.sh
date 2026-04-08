#!/usr/bin/env bash
cd /opt/KGraphVis/backend
source venv/bin/activate
exec gunicorn -w 4 -b 127.0.0.1:5000 app:app
