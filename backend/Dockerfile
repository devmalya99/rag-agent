# Use official lightweight Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements first (better caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy logic
COPY server.py .
COPY extract_transcript.py .

# Expose port (Cloud Run expects 8080 by default)
ENV PORT=8080
EXPOSE 8080

# Run the server
CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0 --port ${PORT}"]

