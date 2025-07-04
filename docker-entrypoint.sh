#!/bin/bash
set -e

echo "Starting Bitaxe Sentry entrypoint script..."

# Create necessary directories
mkdir -p /var/lib/bitaxe

# Create necessary files if they don't exist
if [ ! -f /var/lib/bitaxe/bitaxe_sentry.db ]; then
    echo "Creating empty database file..."
    touch /var/lib/bitaxe/bitaxe_sentry.db
fi

if [ ! -f /var/lib/bitaxe/config.json ]; then
    echo "Creating empty config file..."
    touch /var/lib/bitaxe/config.json
fi

if [ ! -f /var/lib/bitaxe/sentry.pid ]; then
    echo "Creating empty PID file..."
    touch /var/lib/bitaxe/sentry.pid
fi

# Set proper permissions
echo "Setting permissions on data directory..."
chmod -R 777 /var/lib/bitaxe
chown -R appuser:appuser /var/lib/bitaxe

echo "Entrypoint script completed. Starting application..."

# Execute the command passed to the entrypoint
exec "$@" 