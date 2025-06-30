FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY bitaxe_sentry/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY bitaxe_sentry /app/bitaxe_sentry

# Set environment variables
ENV PYTHONPATH=/app

# Create volume for database
VOLUME /app/data

# Set working directory for data
WORKDIR /app/data

# Run the application
CMD ["python", "-m", "bitaxe_sentry.sentry"] 