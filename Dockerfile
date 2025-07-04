FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY bitaxe_sentry/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY bitaxe_sentry /app/bitaxe_sentry

# Set environment variables
ENV PYTHONPATH=/app

# Create non-root user and set up data directory with proper permissions
RUN useradd -u 1000 -m appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /app/data && \
    chmod -R 755 /app/data && \
    chown -R appuser:appuser /app

# Set working directory
WORKDIR /app

# Define volume for persistent data
VOLUME /app/data

# Switch to non-root user
USER appuser

# Run the application
CMD ["python", "-m", "bitaxe_sentry.sentry"] 