# Multi-stage Docker build for Business Intelligence Platform
# Stage 1: Builder - Install dependencies and create wheels
FROM python:3.10.18-slim-bookworm as builder

# Critical Security Updates - Fix CVE-2025-48384, CVE-2025-48385 and kernel vulnerabilities
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /build

# Copy requirements
COPY requirements.txt requirements-prod.txt ./

# Build wheels for faster installs and smaller final image
RUN pip wheel --no-cache-dir --wheel-dir /wheels \
    -r requirements.txt -r requirements-prod.txt

# Stage 2: Runtime - Minimal final image
FROM python:3.10.18-slim-bookworm as runtime

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Critical Security Updates - Update packages without build tools
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
    curl \
    && apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app

# Copy wheels from builder stage
COPY --from=builder /wheels /wheels

# Install from wheels (much faster, smaller)
RUN pip install --no-cache-dir --no-index --find-links /wheels \
    -r /wheels/requirements.txt -r /wheels/requirements-prod.txt || \
    pip install --no-cache-dir /wheels/*.whl && \
    rm -rf /wheels ~/.cache/pip

# Copy application code (only what's needed)
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser app.py app_bi.py conftest.py ./
COPY --chown=appuser:appuser requirements.txt requirements-prod.txt ./

USER appuser

# Expose port
EXPOSE 8501

# Health check - test if Streamlit is responding
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/ || exit 1

# Default command
CMD ["streamlit", "run", "app_bi.py", "--server.address", "0.0.0.0", "--server.port", "8501"]