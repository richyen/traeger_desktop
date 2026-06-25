FROM python:3.9-slim

WORKDIR /app

# Make Python output unbuffered so docker logs show output in real time
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY traeger_client.py .
COPY monitor.py .
COPY app.py .
COPY templates/ templates/
COPY static/ static/

# Create data directory
RUN mkdir -p /app/data

# Expose Flask port
EXPOSE 5000

# Default command (can be overridden in docker-compose)
CMD ["python", "app.py"]
