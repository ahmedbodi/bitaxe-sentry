FROM python:3.11-slim

WORKDIR /app

# Create appuser
RUN adduser --uid 1000 --disabled-password --gecos '' appuser

# Install dependencies *before* switching to appuser
COPY bitaxe_sentry/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Switch to appuser *after* installing everything globally
USER appuser

# Copy app code
COPY bitaxe_sentry /app/bitaxe_sentry

# Set environment
ENV PYTHONPATH=/app
WORKDIR /app

CMD ["python", "-m", "bitaxe_sentry.sentry"]
