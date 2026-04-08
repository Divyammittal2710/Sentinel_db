FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for SQLite
RUN apt-get update && apt-get install -y sqlite3 curl && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything into the container
COPY . .

# Generate the template.db before the server starts
RUN python setup_db.py

EXPOSE 7860

# Environment variables for HF Spaces compatibility
ENV WORKERS=1
ENV PORT=7860
ENV HOST=0.0.0.0

# Launch the SDK server
CMD ["sh", "-c", "PYTHONPATH=. uvicorn server.app:app --host $HOST --port $PORT --workers $WORKERS"]