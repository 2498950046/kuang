FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app/backend_all

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY backend_all/backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

COPY backend_all /app/backend_all

EXPOSE 5000

CMD ["gunicorn", "--chdir", "/app/backend_all/backend", "-w", "2", "-b", "0.0.0.0:5000", "wsgi:application"]
