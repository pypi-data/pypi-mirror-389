# GCS Easy

A simple and easy-to-use Python library for Google Cloud Storage operations with CLI support.

## Features

- 🔐 Simple authentication using service account credentials
- 📤 Upload files with resumable uploads and progress tracking
- 📥 Download files from GCS
- 📋 List bucket contents
- 🗑️ Delete files
- 🔗 Generate signed URLs for secure access
- ⚙️ Flexible configuration via YAML
- 🖥️ Command-line interface for quick operations
- 🔍 Built-in permissions checker

## Installation

### From Source

```bash
git clone https://github.com/juancabrera-r/filedeletemanager.git
cd filedeletemanager
pip install -e .
```

### From PyPI (when published)

```bash
pip install gcs-easy
```

## Configuration

1. Copy `config_example.yml` to `config.yml`:
   ```bash
   cp config_example.yml config.yml
   ```

2. Edit `config.yml` with your settings:
   - Set `GOOGLE_APPLICATION_CREDENTIALS` to the path of your service account JSON file
   - Configure `default_bucket` (bucket name or bucket/path)
   - Adjust other settings as needed

### Configuration Parameters

- `GOOGLE_APPLICATION_CREDENTIALS`: Path to your Google Cloud service account JSON file
- `default_bucket`: Default GCS bucket name (can include a path prefix)
- `location`: GCS location for bucket creation (default: "EU")
- `uniform_access`: Enable uniform bucket-level access (default: true)
- `chunk_size`: Upload chunk size in bytes (default: 8388608)
- `cache_control`: Cache control header for uploaded files
- `signed_url_expires_minutes`: Default expiration time for signed URLs (default: 15)

## Usage

### Command Line Interface

The `gcs-easy` command provides quick access to GCS operations:

```bash
# Upload a file
gcs-easy upload --bucket your-bucket --src /path/to/file.txt --dst remote/path/file.txt

# Make file public during upload
gcs-easy upload --bucket your-bucket --src /path/to/file.txt --dst remote/path/file.txt --public

# Download a file
gcs-easy download --bucket your-bucket --src remote/path/file.txt --dst /local/path/file.txt

# List bucket contents
gcs-easy list --bucket your-bucket --prefix folder/

# Generate signed URL
gcs-easy sign --bucket your-bucket --path remote/path/file.txt --minutes 60

# Check permissions and configuration
gcs-easy permissions
```

### Programmatic Usage

```python
from gcs_easy import GCSClient

# Initialize client (uses config.yml settings)
client = GCSClient()

# Or specify bucket explicitly
client = GCSClient(default_bucket="your-bucket")

# Upload a file
result = client.upload_file(
    local_path="/path/to/file.txt",
    blob_path="remote/path/file.txt",
    make_public=False
)
print(f"Uploaded {result.size} bytes to {result.bucket}/{result.blob}")

# Download a file
local_file = client.download_file(
    blob_path="remote/path/file.txt",
    local_path="/local/path/file.txt"
)

# List files
for blob_name in client.list(prefix="folder/"):
    print(blob_name)

# Check if file exists
if client.exists("remote/path/file.txt"):
    print("File exists")

# Delete a file
client.delete("remote/path/file.txt")

# Generate signed URL
url = client.signed_url("remote/path/file.txt", expires_minutes=30)
print(f"Signed URL: {url}")
```

## Authentication

This library uses Google Cloud service account authentication. You need:

1. A Google Cloud service account with appropriate GCS permissions
2. The service account JSON key file
3. The path to this file in your `config.yml`

### Required Permissions

The service account needs these GCS permissions:
- `storage.objects.create` - Upload files
- `storage.objects.get` - Download files and generate signed URLs
- `storage.objects.list` - List bucket contents
- `storage.objects.delete` - Delete files
- `storage.buckets.get` - Check bucket existence

### Checking Permissions

Use the built-in permissions checker:

```bash
gcs-easy permissions
```

This will analyze your configuration and show required permissions.

## Examples

### Basic Upload/Download

```python
from gcs_easy import GCSClient

client = GCSClient()

# Upload
client.upload_file("local_file.txt", "uploads/file.txt")

# Download
client.download_file("uploads/file.txt", "downloaded_file.txt")
```

### Working with Different Buckets

```python
# Use default bucket from config
client = GCSClient()

# Specify bucket for this operation
client.upload_file("file.txt", "path/file.txt", bucket_name="other-bucket")
```

### Batch Operations

```python
import glob
from pathlib import Path

client = GCSClient()

# Upload all .txt files in a directory
for file_path in Path("data/").glob("*.txt"):
    blob_path = f"data/{file_path.name}"
    client.upload_file(str(file_path), blob_path)
    print(f"Uploaded {file_path.name}")
```

## Development

### Setup Development Environment

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install in development mode
pip install -e ".[test]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest test/test_smoke.py
```

### Building

```bash
# Build distribution
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Author

Juan Manuel Cabrera - juanmanuelcabrera.r@gmail.com