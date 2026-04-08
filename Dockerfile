FROM python:3.10-slim

WORKDIR /app

# System deps: sqlite3 for the DB, curl for health checks
RUN apt-get update && apt-get install -y sqlite3 curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Pre-generate the template database at build time
RUN python setup_db.py

# HF Spaces requires port 7860
EXPOSE 7860

# Start the HTTP server (NOT inference.py)
CMD ["python", "server/app.py"]