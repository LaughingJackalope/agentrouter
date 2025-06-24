# Use an official Python runtime as a parent image
FROM python:3.9-slim-bullseye

# Set environment variables
ENV PYTHONDONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN addgroup --system appuser && adduser --system --no-create-home --ingroup appuser appuser

# Copy requirements first to leverage Docker cache
COPY --chown=appuser:appuser requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Set environment variables
ENV FLASK_APP=agent_management_api.py \
    FLASK_ENV=production \
    PORT=8080

# Expose the port the app runs on
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--worker-class", "sync", "--timeout", "120", "agent_management_api:app"]
