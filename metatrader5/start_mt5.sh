#!/bin/bash

# Start Xvfb
Xvfb :99 -screen 0 1024x768x24 &
export DISPLAY=:99

# Wait for X server
sleep 5

echo "Checking for MT5 installation..."

# Find MT5 terminal executable
MT5_PATH=$(find /root/.wine -name "terminal64.exe" 2>/dev/null | head -n 1)

if [ -z "$MT5_PATH" ]; then
    echo "MT5 not found. Installing MT5..."

    # Install MT5 using the downloaded installer
    if [ -f "/tmp/mt5setup.exe" ]; then
        echo "Running MT5 installer..."
        wine /tmp/mt5setup.exe /auto 2>&1 || true
        sleep 10

        # Search for MT5 again after installation
        MT5_PATH=$(find /root/.wine -name "terminal64.exe" 2>/dev/null | head -n 1)

        if [ -z "$MT5_PATH" ]; then
            echo "MT5 installation failed or terminal not found."
            echo "Container will keep running for debugging..."
            tail -f /dev/null
            exit 0
        fi
    else
        echo "MT5 installer not found at /tmp/mt5setup.exe"
        echo "Container will keep running for debugging..."
        tail -f /dev/null
        exit 0
    fi
fi

echo "Found MT5 at: $MT5_PATH"

# Start MT5 with configuration
if [ -n "$MT5_ACCOUNT" ] && [ -n "$MT5_PASSWORD" ] && [ -n "$MT5_SERVER" ]; then
    echo "Starting MT5 with credentials..."
    wine "$MT5_PATH" \
        /portable \
        /login:${MT5_ACCOUNT} \
        /password:${MT5_PASSWORD} \
        /server:${MT5_SERVER} &
else
    echo "MT5 credentials not provided. Starting MT5 without login..."
    wine "$MT5_PATH" /portable &
fi

# Keep container running
tail -f /dev/null
