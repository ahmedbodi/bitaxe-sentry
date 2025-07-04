FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY bitaxe_sentry/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY bitaxe_sentry /app/bitaxe_sentry

# Set environment variables
ENV PYTHONPATH=/app

# Create data directory with proper permissions
RUN mkdir -p /app/data && \
    chown -R 1000:1000 /app/data && \
    chmod -R 755 /app/data

# Set working directory
WORKDIR /app

# Define volume for persistent data
VOLUME /app/data

# Run the application
CMD ["python", "-m", "bitaxe_sentry.sentry"] 