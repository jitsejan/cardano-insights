FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dbt-athena and dependencies
RUN pip install --no-cache-dir \
    dbt-core==1.10.9 \
    dbt-athena-community==1.8.4 \
    boto3==1.35.84 \
    jinja2==3.1.4

# Copy dbt projects and profiles
COPY transform/ /app/transform/

# Set environment variables
ENV DBT_PROFILES_DIR=/app/transform/profiles
ENV PYTHONPATH=/app

# Create non-root user
RUN useradd --create-home --shell /bin/bash dbt
USER dbt

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=10s --retries=3 \
    CMD dbt --version || exit 1

# Default command runs dbt build for silver models
CMD ["sh", "-c", "envsubst < /app/transform/profiles/profiles.yml.j2 > /app/transform/profiles/profiles.yml && cd /app/transform/dbt_catalyst && dbt deps && dbt build --select tag:silver --target ${DBT_TARGET:-prod}"]