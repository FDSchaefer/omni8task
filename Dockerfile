# Medical Imaging Pipeline Docker Container
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY process_mri.py .

# Create directories for data
RUN mkdir -p /data/input /data/output /data/atlas

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV ATLAS_DIR=/data/atlas

ENTRYPOINT ["python", "process_mri.py"]
CMD ["--help"]
