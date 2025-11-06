# x402tools - Python SDK

Python SDK for the x402 Usage-Based Billing API. Track API usage, manage envelopes, and implement usage-based billing in your Python applications.

## Installation
```bash
pip install x402tools
```

## Quick Start
```python
from x402tools import X402Client

# Initialize the client with your API key
client = X402Client(api_key="your_api_key_here")

# Record usage
usage = client.record_usage(
    envelope_id="your_envelope_id",
    amount=100,
    metadata={"user_id": "123", "action": "api_call"}
)

print(f"Recorded {usage.amount} units of usage")
```

## Features

- ✅ **Envelope Management** - Create and manage usage limit envelopes
- ✅ **Usage Tracking** - Record and retrieve usage data
- ✅ **API Key Management** - Manage authentication keys
- ✅ **Type Hints** - Full type annotation support
- ✅ **Error Handling** - Comprehensive exception classes
- ✅ **Easy Integration** - Simple, intuitive API

## Usage Examples

### Create an Envelope
```python
from x402tools import X402Client

client = X402Client(api_key="your_api_key")

# Create a monthly envelope with 10,000 usage limit
envelope = client.create_envelope(
    name="API Calls",
    limit=10000,
    period="MONTHLY",
    reset_day=1  # Reset on the 1st of each month
)

print(f"Created envelope: {envelope.name} (ID: {envelope.id})")
```

### Record Usage
```python
# Record usage for an envelope
usage = client.record_usage(
    envelope_id=envelope.id,
    amount=50,
    metadata={
        "endpoint": "/api/users",
        "method": "GET",
        "user_id": "user_123"
    }
)

print(f"Usage recorded at {usage.timestamp}")
```

### Get All Envelopes
```python
# Retrieve all envelopes
envelopes = client.get_envelopes()

for env in envelopes:
    print(f"{env.name}: {env.limit} ({env.period})")
```

### Get Usage Statistics
```python
# Get usage stats
stats = client.get_usage_stats()

print(f"Total Usage: {stats.total_usage}")
print(f"Active Envelopes: {stats.active_envelopes}")
```

### Get Usage History
```python
# Get all usage records
all_usage = client.get_usage()

# Get usage for a specific envelope
envelope_usage = client.get_usage(envelope_id="your_envelope_id")

for record in envelope_usage:
    print(f"{record.timestamp}: {record.amount} units")
```

### Update an Envelope
```python
# Update envelope limit
updated = client.update_envelope(
    envelope_id=envelope.id,
    limit=20000
)

print(f"Updated limit to {updated.limit}")
```

### Delete an Envelope
```python
# Delete an envelope
client.delete_envelope(envelope_id=envelope.id)
print("Envelope deleted")
```

### Manage API Keys
```python
# Create a new API key
api_key = client.create_api_key(name="Production Key")
print(f"New API key: {api_key.key}")

# List all API keys
keys = client.get_api_keys()
for key in keys:
    print(f"{key.name}: {key.key}")

# Delete an API key
client.delete_api_key(key_id=api_key.id)
```

## Error Handling
```python
from x402tools import X402Client, AuthenticationError, APIError, RateLimitError

client = X402Client(api_key="your_api_key")

try:
    usage = client.record_usage(
        envelope_id="invalid_id",
        amount=100
    )
except AuthenticationError:
    print("Invalid API key")
except RateLimitError:
    print("Rate limit exceeded, please try again later")
except APIError as e:
    print(f"API Error: {e}")
```

## API Reference

### X402Client

**Constructor:**
```python
X402Client(api_key: str, base_url: str = "https://stakefy-usage-envelope-production.up.railway.app")
```

**Envelope Methods:**
- `get_envelopes() -> List[Envelope]`
- `get_envelope(envelope_id: str) -> Envelope`
- `create_envelope(name: str, limit: int, period: PeriodType, reset_day: Optional[int] = None) -> Envelope`
- `update_envelope(envelope_id: str, **kwargs) -> Envelope`
- `delete_envelope(envelope_id: str) -> None`

**Usage Methods:**
- `record_usage(envelope_id: str, amount: int, metadata: Optional[Dict] = None) -> Usage`
- `get_usage(envelope_id: Optional[str] = None) -> List[Usage]`
- `get_usage_stats() -> UsageStats`

**API Key Methods:**
- `get_api_keys() -> List[ApiKey]`
- `create_api_key(name: str) -> ApiKey`
- `delete_api_key(key_id: str) -> None`

## Data Types

### Envelope
```python
@dataclass
class Envelope:
    id: str
    name: str
    limit: int
    period: Literal["DAILY", "WEEKLY", "MONTHLY", "YEARLY"]
    organization_id: str
    created_at: datetime
    updated_at: datetime
    reset_day: Optional[int] = None
```

### Usage
```python
@dataclass
class Usage:
    id: str
    envelope_id: str
    amount: int
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
```

## Requirements

- Python 3.8+
- requests >= 2.31.0

## License

MIT License

## Support

For issues and questions:
- GitHub Issues: https://github.com/JaspSoe/stakefy-usage-envelope/issues
- Email: support@stakefy.com

## Links

- Homepage: https://stakefy.com
- Documentation: https://github.com/JaspSoe/stakefy-usage-envelope
- PyPI: https://pypi.org/project/x402tools/
