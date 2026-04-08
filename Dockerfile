# Step 1: Use the official Python 3.10 slim image
FROM python:3.10-slim

# Step 2: Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=7860 \
    HOME=/home/user

# Step 3: Install system-level dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Step 4: Create a non-root user
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:${PATH}"
WORKDIR $HOME/app

# Step 5: Install Python dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Step 6: Copy the application code
COPY --chown=user . .

# Step 7: Build the initial database state
# This generates the template.db that your env.py depends on
RUN python setup_db.py

# Step 8: Expose the port
EXPOSE 7860

# Step 9: Start the FastAPI server using inference.py
# This ensures the platform hits your autonomous agent's endpoints
CMD ["uvicorn", "inference:app", "--host", "0.0.0.0", "--port", "7860"]