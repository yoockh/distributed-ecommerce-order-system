FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

COPY docker/app-entrypoint.sh /app/docker/app-entrypoint.sh
RUN chmod +x /app/docker/app-entrypoint.sh

COPY src /app/src

WORKDIR /app/src
ENV PYTHONPATH=/app/src

ENTRYPOINT ["/app/docker/app-entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
