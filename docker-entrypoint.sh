#!/bin/bash
set -e

echo "Starting Bitaxe Sentry entrypoint script..."

# Create necessary files if they don't exist
if [ ! -f /app/data/bitaxe_sentry.db ]; then
    echo "Creating empty database file..."
    touch /app/data/bitaxe_sentry.db
fi

if [ ! -f /app/data/config.json ]; then
    echo "Creating empty config file..."
    touch /app/data/config.json
fi

if [ ! -f /app/data/sentry.pid ]; then
    echo "Creating empty PID file..."
    touch /app/data/sentry.pid
fi

# Set proper permissions
echo "Setting permissions on data directory..."
chmod -R 777 /app/data
chown -R appuser:appuser /app/data

echo "Entrypoint script completed. Starting application..."

# Execute the command passed to the entrypoint
exec "$@" 