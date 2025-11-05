# PyB3 Data Client

Python client library for consuming the B3 Market Data API.

[![PyPI version](https://badge.fury.io/py/pyb3-data-client.svg)](https://pypi.org/project/pyb3-data-client/)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![MIT License](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

---

## Installation

### From PyPI (Recommended)

```bash
pip install pyb3-data-client
```

### From Source

```bash
git clone https://github.com/PedroDnT/pyb3.git
cd pyb3/clients/python
pip install .
```

---

## Usage

```python
from pyb3_data_client import B3Client

client = B3Client(
    api_key="your_api_key",
    base_url="https://your-api.fly.dev"  # Optional, defaults to production
)

# Get daily stock data
df = client.get_daily_data(
    symbols=["PETR4", "VALE3"],
    start_date="2024-01-01",
    end_date="2024-01-31"
)

print(df.head())
```

Returns Polars DataFrame (use `.to_pandas()` for pandas).

---

## Documentation

See main project documentation:

- **[PyB3 Documentation](https://api.b3data.com/docs)** - Complete API reference
- **[Quick Start](../QUICKSTART.md)** - Get started quickly
- **[Deployment](../DEPLOYMENT.md)** - Deploy your own API

---

## Available Methods

```python
# Get daily market data
df = client.get_daily_data(
    symbols=["PETR4", "VALE3"],
    start_date="2024-01-01",
    end_date="2024-12-31",
    format="parquet"  # or "json"
)

# Get symbol metadata
symbols = client.get_symbols(instrument_type="equity")

# Get account information
account = client.get_account_info()

# Get usage statistics
usage = client.get_usage()
```

---

## Requirements

- Python 3.8+
- requests >= 2.31.0
- polars >= 0.20.0
- pyarrow >= 15.0.0

---

## License

MIT License - see [LICENSE](LICENSE) file

---

**Made with ❤️ for the Brazilian financial data community**
