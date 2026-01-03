FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install gitmap packages
RUN pip install --no-cache-dir -e packages/gitmap_core
RUN pip install --no-cache-dir -e apps/cli/gitmap
RUN pip install --no-cache-dir -e apps/mcp/gitmap-mcp

CMD ["python", "main.py"]


