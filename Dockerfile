FROM python:3.10-slim
WORKDIR /app
RUN apt-get update && apt-get install -y sqlite3 curl && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN python setup_db.py
EXPOSE 7860
ENV PYTHONPATH=.
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]