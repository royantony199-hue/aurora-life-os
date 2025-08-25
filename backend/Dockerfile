# Backend Dockerfile for Aurora Life OS
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        curl \
        && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Create necessary directories
RUN mkdir -p /app/uploads /app/logs /app/scripts \
    && chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . .

# Make scripts executable if they exist
RUN if [ -d "scripts" ] && [ -f "scripts/migrate_to_postgresql.py" ]; then chmod +x scripts/migrate_to_postgresql.py; fi

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

# Expose port
EXPOSE ${PORT:-8000}

# Run application
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]