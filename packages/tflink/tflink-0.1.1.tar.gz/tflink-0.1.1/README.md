# tflink

[![PyPI version](https://badge.fury.io/py/tflink.svg)](https://badge.fury.io/py/tflink)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/tflink)](https://pypi.org/project/tflink/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/tflink)](https://pypi.org/project/tflink/)
[![GitHub](https://img.shields.io/github/license/tflink-tmpfile/tflink)](https://github.com/tflink-tmpfile/tflink/blob/main/LICENSE)
[![GitHub issues](https://img.shields.io/github/issues/tflink-tmpfile/tflink)](https://github.com/tflink-tmpfile/tflink/issues)

A simple and easy-to-use Python library for uploading files to [tmpfile.link](https://tmpfile.link) and retrieving download links.

**📦 [View on PyPI](https://pypi.org/project/tflink/) | 📖 [Documentation](https://github.com/tflink-tmpfile/tflink#readme) | 🐛 [Report Issues](https://github.com/tflink-tmpfile/tflink/issues)**

## Features

- Anonymous uploads (files automatically deleted after 7 days)
- Authenticated uploads (requires user ID and authentication token)
- Simple and intuitive API
- Full type hints support
- Comprehensive error handling
- Python 3.8+ support

## Installation

```bash
pip install tflink
```

## Quick Start

### Anonymous Upload

```python
from tflink import TFLinkClient

# Create client
client = TFLinkClient()

# Upload file
result = client.upload('path/to/your/file.pdf')

# Get download links (two formats available)
print(f"Download link: {result.download_link}")  # Human-readable
print(f"Encoded link: {result.download_link_encoded}")  # URL-safe

# File information
print(f"File size: {result.size} bytes")
print(f"File type: {result.file_type}")
print(f"File name: {result.file_name}")
print(f"Uploaded to: {result.uploaded_to}")
```

### Authenticated Upload

```python
from tflink import TFLinkClient

# Create authenticated client
client = TFLinkClient(
    user_id='YOUR_USER_ID',
    auth_token='YOUR_AUTH_TOKEN'
)

# Upload file
result = client.upload('path/to/your/file.pdf')

# Get download links
print(f"Download link: {result.download_link}")  # Human-readable
print(f"Encoded link: {result.download_link_encoded}")  # URL-safe
print(f"Uploaded to: {result.uploaded_to}")  # Shows "user: YOUR_USER_ID"
```

### Custom Filename

```python
from tflink import TFLinkClient

client = TFLinkClient()

# Upload with custom filename
result = client.upload('local_file.txt', filename='custom_name.txt')

# Access both link formats
print(f"Download link: {result.download_link}")
print(f"Encoded link: {result.download_link_encoded}")
print(f"Filename: {result.file_name}")  # Will show 'custom_name.txt'
```

### Using Both Download Links

```python
from tflink import TFLinkClient

client = TFLinkClient()
result = client.upload('document.pdf')

# Standard link (human-readable, good for most uses)
print(f"Standard link: {result.download_link}")
# Example: https://d.tmpfile.link/public/2025-07-31/uuid/document.pdf

# Encoded link (URL-safe, good for APIs and special characters)
print(f"Encoded link: {result.download_link_encoded}")
# Example: https://d.tmpfile.link/public%2F2025-07-31%2Fuuid%2Fdocument.pdf

# Both links work and point to the same file
# Use download_link for simplicity, download_link_encoded for safety
```

## API Documentation

### TFLinkClient

#### Initialization Parameters

- `user_id` (str, optional): User ID for authenticated uploads
- `auth_token` (str, optional): Authentication token for authenticated uploads
- `base_url` (str, optional): API base URL, defaults to `https://tmpfile.link`
- `timeout` (int, optional): Request timeout in seconds, defaults to 300

#### Methods

##### `upload(file_path, filename=None)`

Upload a file to tmpfile.link

**Parameters:**
- `file_path` (str | Path): Path to the file to upload
- `filename` (str, optional): Custom filename

**Returns:**
- `UploadResult`: Object containing upload results

**Raises:**
- `FileNotFoundError`: File does not exist or is not a file
- `UploadError`: Upload failed
- `AuthenticationError`: Authentication failed
- `NetworkError`: Network request failed

##### `is_authenticated()`

Check if the client is configured with authentication credentials

**Returns:**
- `bool`: True if authentication credentials are configured, False otherwise

### UploadResult

Upload result object with the following attributes:

- `file_name` (str): File name
- `download_link` (str): Direct download URL (human-readable, unencoded)
  - Example: `https://d.tmpfile.link/public/2025-07-31/uuid/example.png`
  - **Use this for**: Display to users, clickable links, web browsers
- `download_link_encoded` (str): URL-encoded download link (safe for all contexts)
  - Example: `https://d.tmpfile.link/public%2F2025-07-31%2Fuuid%2Fexample.png`
  - **Use this for**: Programmatic access, API calls, filenames with special characters
- `size` (int): File size in bytes
- `file_type` (str): MIME type
- `uploaded_to` (str): Upload destination (e.g., "public" or "user: USER_ID")

**Note about the two links:**
Both links point to the same file. The difference is URL encoding:
- `download_link`: Contains regular forward slashes (/) - easier to read
- `download_link_encoded`: Forward slashes are encoded as %2F - safer for certain contexts

**Which one should you use?**
- For most cases, use `download_link` (it's simpler and works in browsers)
- Use `download_link_encoded` if you need guaranteed URL safety in all contexts

> 📖 **For a detailed explanation with examples, see [LINKS_EXPLAINED.md](LINKS_EXPLAINED.md)**

## Exception Handling

```python
from tflink import TFLinkClient
from tflink.exceptions import (
    TFLinkError,
    UploadError,
    AuthenticationError,
    FileNotFoundError,
    NetworkError
)

client = TFLinkClient()

try:
    result = client.upload('file.pdf')
    print(f"Upload successful: {result.download_link}")
except FileNotFoundError as e:
    print(f"File not found: {e}")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except UploadError as e:
    print(f"Upload failed: {e}")
except NetworkError as e:
    print(f"Network error: {e}")
except TFLinkError as e:
    print(f"Error occurred: {e}")
```

## Complete Example

```python
from pathlib import Path
from tflink import TFLinkClient
from tflink.exceptions import TFLinkError

def upload_file_example():
    """Complete file upload example"""

    # Create client
    client = TFLinkClient()

    # File to upload
    file_path = Path('document.pdf')

    # Check if file exists
    if not file_path.exists():
        print(f"File does not exist: {file_path}")
        return

    try:
        # Upload file
        print(f"Uploading: {file_path.name}")
        result = client.upload(file_path)

        # Display results
        print(f"✓ Upload successful!")
        print(f"  File name: {result.file_name}")
        print(f"  Download link: {result.download_link}")
        print(f"  File size: {result.size:,} bytes")
        print(f"  File type: {result.file_type}")
        print(f"  Uploaded to: {result.uploaded_to}")

        return result.download_link

    except TFLinkError as e:
        print(f"✗ Upload failed: {e}")
        return None

if __name__ == '__main__':
    upload_file_example()
```

## Development

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Run Tests with Coverage

```bash
pytest --cov=tflink --cov-report=html
```

### Code Formatting

```bash
black tflink tests
```

### Type Checking

```bash
mypy tflink
```

## Build and Publish

### Build Distribution

```bash
python -m build
```

This will create `.tar.gz` and `.whl` files in the `dist/` directory.

### Upload to PyPI

First, make sure `twine` is installed:

```bash
pip install twine
```

Upload to TestPyPI (for testing):

```bash
twine upload --repository testpypi dist/*
```

Upload to production PyPI:

```bash
twine upload dist/*
```

Or use API token (recommended):

```bash
twine upload -u __token__ -p YOUR_PYPI_TOKEN dist/*
```

## License

MIT License

## Contributing

Issues and Pull Requests are welcome!

## Links

- [tmpfile.link Official Website](https://tmpfile.link)
- [API Documentation](https://tmpfile.link)
- [PyPI Project Page](https://pypi.org/project/tflink/)

## Changelog

### 0.1.0 (2025-01-04)

- Initial release
- Support for anonymous and authenticated uploads
- Complete error handling
- Unit test coverage
