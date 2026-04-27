FROM python:3.11-slim

# Instalar dependencias del sistema para PyAudio
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    build-essential \
    portaudio19-dev \
    python3-dev \
    libasound2-dev \
    libportaudio2 \
    libportaudiocpp0 \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8080

ENV FLASK_ENV=production
ENV PORT=8080

# ✅ Usar wsgi.py desde la raíz
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 --worker-class eventlet wsgi:application