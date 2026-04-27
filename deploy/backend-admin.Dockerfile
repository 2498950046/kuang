FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/backend_all

COPY backend_all/backendAdmin/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend_all /app/backend_all
COPY deploy/init-data.sh /usr/local/bin/init-data.sh

RUN chmod +x /usr/local/bin/init-data.sh

EXPOSE 5002

CMD ["gunicorn", "--chdir", "/app/backend_all", "-w", "2", "-b", "0.0.0.0:5002", "backendAdmin.run:app"]
