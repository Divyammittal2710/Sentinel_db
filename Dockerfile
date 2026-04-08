FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y sqlite3 curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python setup_db.py
EXPOSE 3232
# This starts your hardened root-level server
CMD ["python", "inference.py"]