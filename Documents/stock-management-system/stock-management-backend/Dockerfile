# Multi-stage build for production optimization
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies in a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies only and security updates
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    ca-certificates \
    && apt-get upgrade -y \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoremove -y

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set environment variables for production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_ENV=production

# Create non-root user with specific UID/GID for security
RUN groupadd -r appgroup --gid=1000 && \
    useradd -r -g appgroup --uid=1000 --home-dir=/app --shell=/bin/bash appuser

# Set working directory and create necessary directories
WORKDIR /app
RUN mkdir -p /app/logs /app/uploads /app/tmp && \
    chown -R appuser:appgroup /app

# Copy application code with proper ownership
COPY --chown=appuser:appgroup . .

# Set secure file permissions
RUN chmod -R 755 /app && \
    chmod -R 644 /app/src && \
    find /app -name "*.py" -exec chmod 644 {} \; && \
    chmod 755 /app/src/main.py

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 5000

# Add resource limits and security configurations via labels
LABEL maintainer="Stock Management System" \
      version="1.0.0" \
      description="Production-ready Flask backend for Stock Management" \
      security.non-root="true" \
      resources.cpu="1000m" \
      resources.memory="512Mi"

# Enhanced health check with proper timeout and retry logic
HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run the application with Gunicorn for production readiness
# Using multiple workers and proper timeout settings
CMD ["gunicorn", \
     "--bind", "0.0.0.0:5000", \
     "--workers", "2", \
     "--worker-class", "sync", \
     "--worker-connections", "1000", \
     "--timeout", "30", \
     "--keepalive", "2", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--preload", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "--log-level", "info", \
     "src.main:app"]
