FROM ubuntu:22.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN dpkg --add-architecture i386 && \
    apt-get update && apt-get install -y \
    wget \
    xvfb \
    x11vnc \
    wine64 \
    wine32:i386 \
    winetricks \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set up Wine
ENV WINEPREFIX=/root/.wine
ENV WINEARCH=win64
ENV DISPLAY=:99

# Create necessary directories
RUN mkdir -p /root/.wine /config /mt5 /tmp

# Download MT5 installer (but don't install yet - will be done at runtime)
WORKDIR /tmp
RUN wget https://download.mql5.com/cdn/web/metaquotes.software.corp/mt5/mt5setup.exe -O mt5setup.exe

# Initialize Wine prefix
RUN wine wineboot --init 2>&1 || true && sleep 3

# Copy startup script
COPY start_mt5.sh /start_mt5.sh
RUN chmod +x /start_mt5.sh

# Healthcheck - check if Xvfb is running (MT5 will be installed at runtime)
HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD pgrep -f Xvfb || exit 1

# Start MT5
CMD ["/start_mt5.sh"]
