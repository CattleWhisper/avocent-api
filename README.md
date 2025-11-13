# pmCommand REST API

A REST API wrapper for the pmCommand module to control Power Management Units (PDUs) via HTTP requests.

## Features

- **Fetch outlet status**: Get the current status, power consumption, and current for all or specific outlets
- **Control outlets**: Turn outlets on/off individually or in bulk
- **Power cycling**: Cycle (reboot) outlets
- **PDU information**: List all available PDUs with their status

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Set up environment variables for authentication:

```bash
export PM_BASE_URL="https://your-pdu-hostname"
export PM_USERNAME="admin"
export PM_PASSWORD="your-password"
```

## Running the API Server

### Basic Usage

```bash
python src/api.py
```

This will start the server on `http://0.0.0.0:5000`

### Advanced Options

```bash
python src/api.py --host 0.0.0.0 --port 8080 --debug
```

Options:
- `--host`: Host to bind to (default: 0.0.0.0)
- `--port`: Port to bind to (default: 5000)
- `--debug`: Enable debug mode for development

## API Endpoints

### Health Check

**GET** `/api/health`

Check if the API server is running and authenticated.

**Response:**
```json
{
  "status": "healthy",
  "authenticated": true
}
```

---

### List PDUs

**GET** `/api/pdus`

Get a list of all available PDUs with their status.

**Response:**
```json
{
  "pdus": [
    {
      "pdu_id": "power3-r17",
      "vendor": "Avocent",
      "model": "PM3000/10/16A",
      "status": "On Line",
      "outlets": "8/10",
      "current": "4.2",
      "power": "1002.0",
      "alarm": "Normal"
    }
  ]
}
```

---

### List All Outlets

**GET** `/api/outlets`

Get status of all outlets across all PDUs.

**Query Parameters:**
- `pdu_id` (optional): Filter by specific PDU ID
- `outlet_number` (optional): Filter by specific outlet number (requires `pdu_id`)

**Response:**
```json
{
  "outlets": [
    {
      "pdu_id": "power3-r17",
      "outlet_number": "6",
      "name": "HE20-flapsie-L",
      "status": "ON(locked)",
      "current": "0.4",
      "power": "110.0",
      "circuit": "N/A"
    }
  ]
}
```

**Examples:**
```bash
# Get all outlets
curl http://localhost:5000/api/outlets

# Get all outlets from specific PDU
curl http://localhost:5000/api/outlets?pdu_id=power3-r17

# Get specific outlet
curl http://localhost:5000/api/outlets?pdu_id=power3-r17&outlet_number=6
```

---

### Get Outlet Status

**GET** `/api/outlets/<pdu_id>/<outlet_number>`

Get status of a specific outlet.

**Response:**
```json
{
  "pdu_id": "power3-r17",
  "outlet_number": "6",
  "name": "HE20-flapsie-L",
  "status": "ON(locked)",
  "current": "0.4",
  "power": "110.0",
  "circuit": "N/A"
}
```

**Example:**
```bash
curl http://localhost:5000/api/outlets/power3-r17/6
```

---

### Turn On Outlet(s)

**POST** `/api/outlets/on` (Bulk operation)

Turn on one or multiple outlets.

**Request Body:**
```json
{
  "outlets": [
    {"pdu_id": "power1", "outlet_number": "1"},
    {"pdu_id": "power1", "outlet_number": "2"}
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "pdu_id": "power1",
      "outlet_number": "1",
      "action": "on",
      "success": true
    },
    {
      "pdu_id": "power1",
      "outlet_number": "2",
      "action": "on",
      "success": true
    }
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/outlets/on \
  -H "Content-Type: application/json" \
  -d '{"outlets": [{"pdu_id": "power1", "outlet_number": "1"}]}'
```

---

**POST** `/api/outlets/<pdu_id>/<outlet_number>/on` (Single outlet)

Turn on a specific outlet.

**Response:**
```json
{
  "pdu_id": "power1",
  "outlet_number": "1",
  "action": "on",
  "success": true
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/outlets/power1/1/on
```

---

### Turn Off Outlet(s)

**POST** `/api/outlets/off` (Bulk operation)

Turn off one or multiple outlets.

**Request Body:**
```json
{
  "outlets": [
    {"pdu_id": "power1", "outlet_number": "1"},
    {"pdu_id": "power1", "outlet_number": "2"}
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "pdu_id": "power1",
      "outlet_number": "1",
      "action": "off",
      "success": true
    }
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/outlets/off \
  -H "Content-Type: application/json" \
  -d '{"outlets": [{"pdu_id": "power1", "outlet_number": "1"}]}'
```

---

**POST** `/api/outlets/<pdu_id>/<outlet_number>/off` (Single outlet)

Turn off a specific outlet.

**Example:**
```bash
curl -X POST http://localhost:5000/api/outlets/power1/1/off
```

---

### Cycle Outlet(s)

**POST** `/api/outlets/cycle` (Bulk operation)

Power cycle (turn off then on) one or multiple outlets.

**Request Body:**
```json
{
  "outlets": [
    {"pdu_id": "power1", "outlet_number": "1"},
    {"pdu_id": "power1", "outlet_number": "2"}
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "pdu_id": "power1",
      "outlet_number": "1",
      "action": "cycle",
      "success": true
    }
  ]
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/api/outlets/cycle \
  -H "Content-Type: application/json" \
  -d '{"outlets": [{"pdu_id": "power1", "outlet_number": "1"}]}'
```

---

**POST** `/api/outlets/<pdu_id>/<outlet_number>/cycle` (Single outlet)

Power cycle a specific outlet.

**Example:**
```bash
curl -X POST http://localhost:5000/api/outlets/power1/1/cycle
```

---

## Error Handling

The API uses standard HTTP status codes:

- `200 OK`: Request successful
- `207 Multi-Status`: Bulk operation with partial success (some outlets succeeded, some failed)
- `400 Bad Request`: Invalid request or pmCommand error
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Health check failed

**Error Response Format:**
```json
{
  "error": "Error message description"
}
```

**Partial Success Response (207):**
```json
{
  "results": [
    {
      "pdu_id": "power1",
      "outlet_number": "1",
      "action": "on",
      "success": true
    }
  ],
  "errors": [
    {
      "pdu_id": "power1",
      "outlet_number": "99",
      "error": "Outlet not found"
    }
  ]
}
```

## Configuration

Environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PM_BASE_URL` | Base URL of the PDU/Power Management system | `https://localhost` |
| `PM_USERNAME` | Username for authentication | `admin` |
| `PM_PASSWORD` | Password for authentication | `admin` |

## Examples

### Python

```python
import requests

base_url = "http://localhost:5000"

# Get all outlets
response = requests.get(f"{base_url}/api/outlets")
outlets = response.json()["outlets"]

# Turn on an outlet
requests.post(f"{base_url}/api/outlets/power1/1/on")

# Turn off multiple outlets
requests.post(
    f"{base_url}/api/outlets/off",
    json={
        "outlets": [
            {"pdu_id": "power1", "outlet_number": "1"},
            {"pdu_id": "power1", "outlet_number": "2"}
        ]
    }
)

# Cycle an outlet
requests.post(f"{base_url}/api/outlets/power1/1/cycle")
```

### JavaScript (fetch)

```javascript
const baseUrl = "http://localhost:5000";

// Get all outlets
const outlets = await fetch(`${baseUrl}/api/outlets`)
  .then(res => res.json());

// Turn on an outlet
await fetch(`${baseUrl}/api/outlets/power1/1/on`, {
  method: 'POST'
});

// Turn off multiple outlets
await fetch(`${baseUrl}/api/outlets/off`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    outlets: [
      {pdu_id: "power1", outlet_number: "1"},
      {pdu_id: "power1", outlet_number: "2"}
    ]
  })
});
```

### curl

```bash
# Health check
curl http://localhost:5000/api/health

# List PDUs
curl http://localhost:5000/api/pdus

# Get all outlets
curl http://localhost:5000/api/outlets

# Get specific outlet status
curl http://localhost:5000/api/outlets/power1/1

# Turn on outlet
curl -X POST http://localhost:5000/api/outlets/power1/1/on

# Turn off outlet
curl -X POST http://localhost:5000/api/outlets/power1/1/off

# Cycle outlet
curl -X POST http://localhost:5000/api/outlets/power1/1/cycle

# Bulk operations
curl -X POST http://localhost:5000/api/outlets/on \
  -H "Content-Type: application/json" \
  -d '{"outlets": [{"pdu_id": "power1", "outlet_number": "1"}, {"pdu_id": "power1", "outlet_number": "2"}]}'
```

## Security Considerations

- This API does not implement authentication/authorization. It relies on the underlying pmCommand authentication.
- Consider deploying behind a reverse proxy (nginx, Apache) with proper authentication
- Use HTTPS in production
- Restrict access using firewall rules or network segmentation
- Consider implementing rate limiting for production use

## License

Same license as the pmCommand module (MIT License)
