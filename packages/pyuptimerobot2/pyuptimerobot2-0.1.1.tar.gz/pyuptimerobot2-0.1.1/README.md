# pyuptimerobot2

[![PyPI version](https://badge.fury.io/py/pyuptimerobot2.svg)](https://badge.fury.io/py/pyuptimerobot2)
[![Python Versions](https://img.shields.io/pypi/pyversions/pyuptimerobot2.svg)](https://pypi.org/project/pyuptimerobot2/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A comprehensive Python client for UptimeRobot API v3. This library provides complete access to all UptimeRobot monitoring features including monitors, alert contacts, maintenance windows, and status pages.

## Features

- 🔧 **Complete API Coverage**: All UptimeRobot API v3 endpoints implemented
- 📊 **Monitor Management**: Create, read, update, delete monitors with full configuration
- 🔔 **Alert Contacts**: Email, SMS, webhook, Slack, Teams, and Twitter notifications
- 🔧 **Maintenance Windows**: Schedule maintenance periods to pause monitoring
- 📄 **Status Pages**: Create and manage public status pages
- 👤 **Account Management**: Access account details and API key information
- ⚡ **Rate Limit Handling**: Built-in awareness of UptimeRobot's rate limits
- 🛡️ **Error Handling**: Comprehensive error handling with descriptive messages
- 📝 **Type Hints**: Full type annotations for better IDE support

## Installation

```bash
pip install pyuptimerobot2
```

Or install from source:

```bash
git clone https://github.com/emadomedher/pyUptimerobot.git
cd pyuptimerobot2
pip install -r requirements.txt
pip install .
```

## Quick Start

### Basic Usage

```python
from uptimerobot_api import UptimeRobotClient

# Initialize the client with your API key
client = UptimeRobotClient(api_key="your_api_key_here")

try:
    # Get all monitors
    monitors = client.get_monitors()
    print(f"Found {len(monitors['data'])} monitors")

    # Create a new HTTP monitor
    new_monitor = client.new_monitor(
        friendly_name="My Website",
        url="https://example.com",
        type=1,  # HTTP monitor
        interval=300  # 5 minutes
    )
    print(f"Created monitor: {new_monitor}")

    # Get account details
    account = client.get_account_details()
    print(f"Account: {account}")

finally:
    client.close()
```

### Advanced Monitor Configuration

```python
from uptimerobot_api import UptimeRobotClient

client = UptimeRobotClient(api_key="your_api_key")

# Create a monitor with keyword monitoring
monitor = client.new_monitor(
    friendly_name="API Health Check",
    url="https://api.example.com/health",
    type=2,  # Keyword monitor
    keyword_type=1,  # Should contain keyword
    keyword_value='"status":"healthy"',
    interval=60,  # Check every minute
    timeout=10,   # 10 second timeout
    alert_contacts="12345-67890"  # Alert contact IDs
)

print(f"Created keyword monitor: {monitor}")
```

### Alert Contact Setup

```python
from uptimerobot_api import UptimeRobotClient

client = UptimeRobotClient(api_key="your_api_key")

# Create a webhook alert contact
webhook = client.new_alert_contact(
    friendly_name="Slack Webhook",
    type=5,  # Webhook
    value="https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
)

# Create an email alert contact
email = client.new_alert_contact(
    friendly_name="Admin Email",
    type=1,  # Email
    value="admin@example.com"
)

print(f"Created webhook: {webhook}")
print(f"Created email: {email}")
```

## API Reference

### UptimeRobotClient

The main client class for interacting with UptimeRobot API.

#### Initialization

```python
client = UptimeRobotClient(api_key="your_api_key")
```

#### Monitor Methods

- `get_monitors(monitors=None, types=None, statuses=None, keyword=None, alert_contacts=None, logs=None, logs_limit=None, response_times=None, response_times_limit=None, response_times_average=None, response_times_start_date=None, response_times_end_date=None, offset=None, limit=None)`: Get monitors with filtering
- `new_monitor(friendly_name, url, type, sub_type=None, port=None, keyword_type=None, keyword_value=None, interval=None, timeout=None, alert_contacts=None, monitor_group_id=None)`: Create a new monitor
- `edit_monitor(id, friendly_name=None, url=None, type=None, interval=None, timeout=None, alert_contacts=None)`: Update a monitor
- `delete_monitor(id)`: Delete a monitor
- `reset_monitor(id)`: Reset monitor statistics

#### Alert Contact Methods

- `get_alert_contacts(alert_contacts=None)`: Get alert contacts
- `new_alert_contact(friendly_name, type, value)`: Create an alert contact
- `edit_alert_contact(id, friendly_name=None, type=None, value=None)`: Update an alert contact
- `delete_alert_contact(id)`: Delete an alert contact

#### Maintenance Window Methods

- `get_maintenance_windows(maintenance_windows=None)`: Get maintenance windows
- `new_maintenance_window(friendly_name, type, value, duration, start_time=None, status=None)`: Create a maintenance window
- `edit_maintenance_window(id, friendly_name=None, type=None, value=None, duration=None)`: Update a maintenance window
- `delete_maintenance_window(id)`: Delete a maintenance window

#### Status Page Methods

- `get_status_pages(status_pages=None)`: Get status pages
- `new_status_page(friendly_name, monitors)`: Create a status page
- `edit_status_page(id, friendly_name=None, monitors=None, status_page_password=None)`: Update a status page
- `delete_status_page(id)`: Delete a status page

#### Account Methods

- `get_account_details()`: Get account information
- `get_api_key_details()`: Get API key information

### Monitor Types

| Value | Type | Description |
|-------|------|-------------|
| 1 | HTTP(S) | Standard website monitoring |
| 2 | Keyword | Monitors for specific text content |
| 3 | Ping | ICMP ping monitoring |
| 4 | Port | TCP port monitoring |
| 5 | Heartbeat | Custom heartbeat monitoring |

### Monitor Statuses

| Value | Status | Description |
|-------|--------|-------------|
| 0 | Paused | Monitor is paused |
| 1 | Not checked yet | Monitor hasn't been checked |
| 2 | Up | Monitor is responding |
| 8 | Seems down | Monitor appears down |
| 9 | Down | Monitor is down |

### Alert Contact Types

| Value | Type | Description |
|-------|------|-------------|
| 1 | Email | Email notifications |
| 2 | SMS | SMS notifications |
| 3 | Twitter DM | Direct messages |
| 5 | Webhook | HTTP webhook |
| 6 | Push | Push notifications |
| 9 | Slack | Slack integration |
| 12 | Microsoft Teams | Teams integration |

## Rate Limits

UptimeRobot enforces rate limits based on your plan:

| Plan | Rate Limit |
|------|------------|
| **Free** | 10 requests/minute |
| **Pro** | (monitor count × 2) requests/minute, max 5000/minute |

The client includes rate limit information in response headers when available.

## Error Handling

```python
from uptimerobot_api import UptimeRobotClient
import requests

client = UptimeRobotClient(api_key="your_api_key")

try:
    monitors = client.get_monitors()
    print(f"Success: {monitors}")

except ValueError as e:
    # API-specific errors (invalid API key, not found, etc.)
    print(f"API Error: {e}")

except requests.RequestException as e:
    # Network/connection errors
    print(f"Network Error: {e}")
```

## Examples

See the `examples/` directory for complete usage examples:

- `basic_monitoring.py`: Basic monitor CRUD operations
- `alert_contacts.py`: Setting up various alert contact types
- `maintenance_windows.py`: Managing maintenance schedules
- `status_pages.py`: Creating and managing status pages
- `bulk_operations.py`: Performing operations on multiple monitors

### Basic Monitoring Example

```python
from uptimerobot_api import UptimeRobotClient

client = UptimeRobotClient(api_key="your_api_key")

# Get all monitors
monitors = client.get_monitors()
for monitor in monitors['data']:
    print(f"Monitor: {monitor['friendly_name']} - Status: {monitor['status']}")

# Create a new monitor
new_monitor = client.new_monitor(
    friendly_name="Production API",
    url="https://api.example.com/health",
    type=1,
    interval=300
)

# Update the monitor
client.edit_monitor(
    id=new_monitor['data']['id'],
    friendly_name="Production API v2"
)

# Clean up
client.delete_monitor(new_monitor['data']['id'])
client.close()
```

## Development

### Setup Development Environment

```bash
git clone https://github.com/emadomedher/pyUptimerobot.git
cd pyuptimerobot2
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This library is not officially affiliated with or endorsed by UptimeRobot. Use this library at your own risk and in accordance with UptimeRobot's Terms of Service.

## Support

- 📖 [Documentation](https://github.com/emadomedher/pyUptimerobot#readme)
- 🐛 [Bug Reports](https://github.com/emadomedher/pyUptimerobot/issues)
- 💬 [Discussions](https://github.com/emadomedher/pyUptimerobot/discussions)

## Changelog

### [0.1.0] - 2025-11-03
- Initial release
- Complete UptimeRobot API v3 implementation
- Monitor management (CRUD operations)
- Alert contact management
- Maintenance window management
- Status page management
- Account information access
- Comprehensive error handling
- Rate limit awareness
