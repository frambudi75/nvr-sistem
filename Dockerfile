FROM python:3.11-slim

# Install ffmpeg and openssl
RUN apt-get update && \
    apt-get install -y ffmpeg openssl && \
    rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY ./app /app
COPY config.json /config.json

# Set environment variable to ensure python output is unbuffered
ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
