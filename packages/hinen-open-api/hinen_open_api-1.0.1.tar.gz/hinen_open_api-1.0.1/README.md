# Hinen Open API Client

A Python client library for the Hinen Open API.

## Installation

```bash
pip install hinen-open-api
```

## Usage

```python
import asyncio
from hinen_open_api import HinenOpen

async def main():
    async with HinenOpen(
        host="https://api.hinen.com",
        app_id="your_app_id",
        app_secret="your_app_secret"
    ) as client:
        # Set user authentication if needed
        await client.set_user_authentication(
            token="user_token",
            refresh_token="refresh_token"
        )
        
        # Use the client to make requests
        print("Hinen Open API client initialized successfully!")

if __name__ == "__main__":
    asyncio.run(main())
```

## Development

To install the package in development mode:

```bash
pip install -e .
```

To run tests:

```bash
pytest tests/
```

This project uses `pyproject.toml` for packaging configuration instead of `setup.py`.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
