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
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install MetaTrader5 from wheel file
RUN pip install --no-cache-dir https://github.com/5k3105/mt5linux/raw/master/MetaTrader5-5.0.45-cp311-cp311-linux_x86_64.whl

# Copy the rest of the application
COPY . .

# Create a non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Health check endpoint
EXPOSE 8000

# Start the application
CMD ["python", "main.py"]