FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ .

# Set environment variables (can be overridden at runtime)
ENV PM_BASE_URL=https://localhost
ENV PM_USERNAME=admin
ENV PM_PASSWORD=admin
ENV FLASK_HOST=0.0.0.0
ENV FLASK_PORT=5000

# Expose port
EXPOSE 5000

# Run the API
CMD ["python", "api.py", "--host", "0.0.0.0", "--port", "5000"]
