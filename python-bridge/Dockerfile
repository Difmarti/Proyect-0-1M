FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    gcc \
    g++ \
    postgresql-client \
    curl \
    wget \
    build-essential \
    python3-dev \
    libxcb1 \
    xvfb \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Set up virtual display for MetaTrader5
ENV DISPLAY=:99
RUN mkdir -p /tmp/.X11-unix && \
    chmod 1777 /tmp/.X11-unix

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Start Xvfb in the background when container starts
CMD Xvfb :99 -screen 0 1024x768x16 & python main.py

# Copy the rest of the application
COPY . .

# Create a non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Health check endpoint
EXPOSE 8000

# Start the application
CMD ["python", "main.py"]