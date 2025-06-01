# Multi-stage build for optimized production image
FROM python:3.12-slim as builder

# Install build dependencies for lxml and other packages
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libxml2-dev \
    libxslt-dev \
    libssl-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.12-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libxml2 \
    libxslt1.1 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p logs data models && chown -R appuser:appuser logs data models

# Set Python path
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

# Set production environment variables
ENV ENVIRONMENT=production
ENV LOG_LEVEL=INFO
ENV DATABASE_PATH=/app/data/esg_data.db
ENV UPSTASH_UPSTASH_REDIS_URL=redis://localhost:6379

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Copy startup script
COPY --chown=appuser:appuser deployment/start_production.sh /app/start_production.sh
USER root
RUN chmod +x /app/start_production.sh
USER appuser

# Run the application
CMD ["/app/start_production.sh"] 