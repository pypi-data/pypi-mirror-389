# LogVictoriaLogs

Python client library for integrating with VictoriaLogs, a high-performance log database and search solution.

## Features

- Easy integration with VictoriaLogs
- Support for multiple logging protocols (HTTP, Syslog)
- Automatic caller information capture
- Python logging module integration
- Structured logging with rich context information

## Installation

```bash
pip install LogVictoriaLogs
```

## Usage

### Basic Usage

```python
from LogVictoriaLogs import VictoriaLogsClient

# Create client instance
client = VictoriaLogsClient("victorialogs-host", 9428, 514)

# Send basic logs
client.send_logs([
    {"message": "Hello VictoriaLogs", "level": "info", "service": "my-service"}
])

# Log with context information
client.log_with_context(
    "User login successful",
    level="info",
    service="auth-service",
    user_id="123",
    ip_address="192.168.1.1"
)
```

### Python Logging Integration

```python
import logging
from LogVictoriaLogs import VictoriaLogsClient

# Create client
client = VictoriaLogsClient("victorialogs-host", 9428, 514)

# Configure logging
logger = logging.getLogger("MyApp")
logger.setLevel(logging.INFO)

# Add VictoriaLogs handler
handler = client.setup_logging_handler(service="my-application")
logger.addHandler(handler)

# Use standard logging
logger.info("Application started")
logger.error("Something went wrong")
```

## License

MIT