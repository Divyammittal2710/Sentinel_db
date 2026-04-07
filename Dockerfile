# Step 1: Use the official Python 3.10 slim image for a small, fast container
FROM python:3.10-slim

# Step 2: Set environment variables for Python and OpenEnv requirements
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    HOME=/home/user

# Step 3: Install system-level dependencies (SQLite3 is required for our DB)
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Step 4: Create a non-root user (Mandatory for Hugging Face security)
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"
WORKDIR $HOME/app

# Step 5: Install Python dependencies
# We copy requirements first to leverage Docker's cache layers
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Step 6: Copy the rest of your application code
COPY --chown=user . .

# Step 7: Build the initial database state
# This ensures setup_db.py runs during the build, not just at runtime
RUN python setup_db.py

# Step 8: Expose the port required by Hugging Face Spaces
EXPOSE 7860

# Step 9: Start the FastAPI server (app.py) using Uvicorn
# This allows the 'validate-submission.sh' script to ping your /reset endpoint
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]