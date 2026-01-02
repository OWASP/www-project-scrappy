FROM python:3.11-slim

LABEL maintainer="OWASP ScrapPY Project"
LABEL description="ScrapPY Web API - Secure PDF wordlist generator"

# Security: Run as non-root user
RUN useradd --create-home --shell /bin/bash scrappy

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better layer caching
COPY requirements.txt .
COPY scrappy_web/requirements.txt ./scrappy_web/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -r scrappy_web/requirements.txt \
    && pip install --no-cache-dir pytest httpx

# Copy application code
COPY ScrapPY.py .
COPY scrappy_web/ ./scrappy_web/

# Create upload directory with proper permissions
RUN mkdir -p /app/temp_uploads && chown -R scrappy:scrappy /app

# Switch to non-root user
USER scrappy

# Environment variables (override in production)
ENV SCRAPPY_UPLOAD_DIR=/app/temp_uploads
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/docs')" || exit 1

# Run with uvicorn
CMD ["python", "-m", "uvicorn", "scrappy_web.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
