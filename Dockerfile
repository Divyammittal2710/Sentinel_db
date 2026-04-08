FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y sqlite3 curl && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files to the root of /app
COPY . .

# Initialize the database
RUN python setup_db.py

# Expose the mandatory port
EXPOSE 7860

# Start the application via the script entry point
CMD ["python", "inference.py"]