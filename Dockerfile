# 📌 Dockerfile for Zelda-like Game Application
FROM python:3.10-slim

# 🧰 Install system dependencies for pygame
RUN apt-get update && apt-get install -y \
    build-essential \
    libsdl2-dev \
    libsdl2-image-dev \
    libsdl2-mixer-dev \
    libsdl2-ttf-dev \
    libfreetype6-dev \
    libportmidi-dev \
    libjpeg-dev \
    python3-dev \
    python3-numpy \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# 🔧 Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 📁 Set up working directory
WORKDIR /app

# 📋 Copy game files
COPY . /app

# 🧪 Set environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV SDL_VIDEODRIVER=dummy

# 🎮 Expose port for potential web interface
EXPOSE 8080

# 🚀 Health check to verify game can load
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from src.core.config_loader import load_config; load_config(); print('OK')" || exit 1

# 🎯 Default command to run the game
CMD [ "pytest", "-q", "tests/" ]