# pmCommand REST API - Quick Start Guide

## 🚀 Quick Start

### Option 1: Run Directly with Python

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set environment variables:**
   ```bash
   export PM_BASE_URL="https://your-pdu-hostname"
   export PM_USERNAME="admin"
   export PM_PASSWORD="your-password"
   ```

3. **Start the API server:**
   ```bash
   python src/api.py
   ```

4. **Test the API:**
   ```bash
   curl http://localhost:5000/api/health
   ```

### Option 2: Run with Docker

1. **Build the Docker image:**
   ```bash
   docker build -t avocent-api .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     -p 5000:5000 \
     -e PM_BASE_URL="https://your-pdu-hostname" \
     -e PM_USERNAME="admin" \
     -e PM_PASSWORD="your-password" \
     --name avocent-api \
     avocent-api
   ```

3. **Test the API:**
   ```bash
   curl http://localhost:5000/api/health
   ```

4. **View logs:**
   ```bash
   docker logs -f avocent-api
   ```

5. **Stop the container:**
   ```bash
   docker stop avocent-api
   docker rm avocent-api
   ```

## 📝 Common Operations

### Check System Status

```bash
# Health check
curl http://localhost:5000/api/health

# List all PDUs
curl http://localhost:5000/api/pdus

# List all outlets with status
curl http://localhost:5000/api/outlets
```

### Control Single Outlet

```bash
# Get outlet status
curl http://localhost:5000/api/outlets/power1/1

# Turn outlet ON
curl -X POST http://localhost:5000/api/outlets/power1/1/on

# Turn outlet OFF
curl -X POST http://localhost:5000/api/outlets/power1/1/off

# Cycle (reboot) outlet
curl -X POST http://localhost:5000/api/outlets/power1/1/cycle
```

### Control Multiple Outlets

```bash
# Turn on multiple outlets
curl -X POST http://localhost:5000/api/outlets/on \
  -H "Content-Type: application/json" \
  -d '{
    "outlets": [
      {"pdu_id": "power1", "outlet_number": "1"},
      {"pdu_id": "power1", "outlet_number": "2"},
      {"pdu_id": "power2", "outlet_number": "3"}
    ]
  }'

# Turn off multiple outlets
curl -X POST http://localhost:5000/api/outlets/off \
  -H "Content-Type: application/json" \
  -d '{
    "outlets": [
      {"pdu_id": "power1", "outlet_number": "1"},
      {"pdu_id": "power1", "outlet_number": "2"}
    ]
  }'

# Cycle multiple outlets
curl -X POST http://localhost:5000/api/outlets/cycle \
  -H "Content-Type: application/json" \
  -d '{
    "outlets": [
      {"pdu_id": "power1", "outlet_number": "1"}
    ]
  }'
```

## 🔧 Troubleshooting

### API server won't start

1. Check if port 5000 is already in use:
   ```bash
   lsof -i :5000
   ```

2. Use a different port:
   ```bash
   python src/api.py --port 8080
   ```

### Authentication errors

1. Verify your credentials are correct
2. Check that the PM_BASE_URL is accessible
3. Check API logs for detailed error messages

### Connection refused

1. Make sure the API server is running
2. Check firewall settings
3. Verify the URL and port

## 📚 More Information

See [README.md](README.md) for complete API documentation including:
- Full endpoint reference
- Request/response examples
- Error handling
- Security considerations
- Integration examples in multiple languages
