FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use a non-root user
RUN useradd -m appuser
USER appuser

EXPOSE 8000
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn","-w","3","-b","0.0.0.0:8000","wsgi:app"]
