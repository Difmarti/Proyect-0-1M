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
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create logs directory
RUN mkdir -p /app/logs && chmod 777 /app/logs

# Health check endpoint
EXPOSE 8000

# Start the application
CMD ["python", "main.py"]