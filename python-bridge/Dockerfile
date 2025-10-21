FROM python:3.11-slim

# Install system dependencies including Wine
RUN dpkg --add-architecture i386 && \
    apt-get update && \
    apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    wget \
    software-properties-common \
    gnupg2 \
    && wget -nc https://dl.winehq.org/wine-builds/winehq.key && \
    apt-key add winehq.key && \
    echo "deb https://dl.winehq.org/wine-builds/debian/ bullseye main" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y --install-recommends winehq-stable && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download and install MT4
RUN mkdir -p /root/.wine/drive_c/Program\ Files/MetaTrader\ 4/ && \
    wget -O mt4setup.exe https://download.mql5.com/cdn/web/metaquotes.software.corp/mt4/mt4setup.exe && \
    wine mt4setup.exe /auto

# Copy the rest of the application
COPY . .

# Create a non-root user
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Health check endpoint
EXPOSE 8000

# Start the application
CMD ["python", "main.py"]