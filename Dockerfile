FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    gcc \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/staticfiles && python manage.py collectstatic --noinput || true

EXPOSE 8000

CMD ["sh", "-c", "gunicorn proyecto_acoso.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 120"]