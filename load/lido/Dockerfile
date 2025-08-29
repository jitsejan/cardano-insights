FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY load/lido/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy pipeline code
COPY load/ /app/load/

# Set Python path
ENV PYTHONPATH=/app

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash pipeline
USER pipeline

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import dlt, boto3; print('OK')" || exit 1

# Run the pipeline
ENTRYPOINT ["python", "load/lido/pipeline.py"]