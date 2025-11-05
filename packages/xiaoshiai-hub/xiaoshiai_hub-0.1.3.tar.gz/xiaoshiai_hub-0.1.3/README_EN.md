# XiaoShi AI Hub Python SDK

[![PyPI version](https://badge.fury.io/py/xiaoshiai-hub.svg)](https://badge.fury.io/py/xiaoshiai-hub)
[![Python Support](https://img.shields.io/pypi/pyversions/xiaoshiai-hub.svg)](https://pypi.org/project/xiaoshiai-hub/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

A powerful Python library for interacting with XiaoShi AI Hub platform. It provides easy-to-use APIs for uploading, downloading, and encrypting models and datasets.

English | [简体中文](README.md)

## ✨ Features

- 🚀 **Easy to Use** - Hugging Face Hub-like API design
- 📥 **Download** - Download single files or entire repositories
- 📤 **Upload** - Upload files and folders to repositories
- 🔐 **Encryption** - Built-in support for multiple encryption algorithms (AES, SM4, RSA, SM2)
- 🎯 **Pattern Matching** - Filter files using allow/ignore patterns
- 📊 **Progress Bars** - Visual progress tracking for downloads and uploads
- 🔑 **Multiple Auth Methods** - Support for username/password and token authentication
- 🌐 **Environment Variables** - Flexible Hub URL configuration
- 💾 **Caching** - Efficient file caching mechanism
- 🔍 **Type Hints** - Full type annotations for better IDE support

## 📦 Installation

### Basic Installation (Download Only)

```bash
pip install xiaoshiai-hub
```

### Full Installation (Including Upload)

```bash
pip install xiaoshiai-hub[upload]
```

### Development Installation

```bash
pip install xiaoshiai-hub[dev]
```

### Complete Installation (All Features)

```bash
pip install xiaoshiai-hub[all]
```

## 🚀 Quick Start

### Download a Single File

```python
from xiaoshiai_hub import moha_hub_download

# Download a single file
file_path = moha_hub_download(
    repo_id="demo/demo",
    filename="config.yaml",
    repo_type="models",  # or "datasets"
    username="your-username",
    password="your-password",
)
print(f"File downloaded to: {file_path}")
```

### Download Entire Repository

```python
from xiaoshiai_hub import snapshot_download

# Download entire repository
repo_path = snapshot_download(
    repo_id="demo/demo",
    repo_type="models",
    username="your-username",
    password="your-password",
)
print(f"Repository downloaded to: {repo_path}")
```

### Download with Filters

```python
from xiaoshiai_hub import snapshot_download

# Download only YAML and Markdown files
repo_path = snapshot_download(
    repo_id="demo/demo",
    allow_patterns=["*.yaml", "*.yml", "*.md"],
    ignore_patterns=[".git*", "*.log"],
    username="your-username",
    password="your-password",
)
```

### Upload a File

```python
from xiaoshiai_hub import upload_file

# Upload a single file
commit_hash = upload_file(
    path_or_fileobj="./config.yaml",
    path_in_repo="config.yaml",
    repo_id="demo/my-model",
    repo_type="models",
    commit_message="Upload config file",
    username="your-username",
    password="your-password",
)
print(f"Commit hash: {commit_hash}")
```

### Upload a Folder

```python
from xiaoshiai_hub import upload_folder

# Upload entire folder
commit_hash = upload_folder(
    folder_path="./my_model",
    repo_id="demo/my-model",
    repo_type="models",
    commit_message="Upload model files",
    ignore_patterns=["*.log", ".git*"],  # Ignore these files
    username="your-username",
    password="your-password",
)
print(f"Commit hash: {commit_hash}")
```

### Encrypted Upload and Download

```python
from xiaoshiai_hub import upload_file, moha_hub_download
from xiaoshiai_hub.encryption import EncryptionAlgorithm

# Upload encrypted file
commit_hash = upload_file(
    path_or_fileobj="./secret.txt",
    path_in_repo="secret.txt",
    repo_id="demo/encrypted-repo",
    encryption_key="your-32-character-secret-key",
    encryption_algorithm=EncryptionAlgorithm.AES_256_CBC,
    username="your-username",
    password="your-password",
)

# Download and decrypt file
file_path = moha_hub_download(
    repo_id="demo/encrypted-repo",
    filename="secret.txt",
    decryption_key="your-32-character-secret-key",
    decryption_algorithm=EncryptionAlgorithm.AES_256_CBC,
    username="your-username",
    password="your-password",
)
```

### Using HubClient API

```python
from xiaoshiai_hub import HubClient

# Create client
client = HubClient(
    username="your-username",
    password="your-password",
)

# Get repository info
repo_info = client.get_repository_info("demo", "models", "my-model")
print(f"Repository name: {repo_info.name}")
print(f"Organization: {repo_info.organization}")

# List branches
branches = client.list_branches("demo", "models", "my-model")
for branch in branches:
    print(f"Branch: {branch.name} (commit: {branch.commit_sha})")

# Browse repository content
content = client.get_repository_content("demo", "models", "my-model", "main")
for entry in content.entries:
    print(f"{entry.type}: {entry.name}")
```

## 🔐 Encryption

The SDK supports multiple encryption algorithms:

### Symmetric Encryption

- **AES-256-CBC** - Standard AES encryption
- **AES-256-GCM** - AES encryption with authentication
- **SM4-CBC** - Chinese national standard SM4 encryption
- **SM4-GCM** - SM4 encryption with authentication

### Asymmetric Encryption

- **RSA-OAEP** - RSA encryption (recommended)
- **RSA-PKCS1V15** - RSA encryption (compatibility)
- **SM2** - Chinese national standard SM2 encryption

### Generate Encryption Keys

```python
import secrets
import string

# Generate symmetric key (32 characters)
symmetric_key = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
print(f"Symmetric key: {symmetric_key}")

# Generate RSA key pair
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)
public_key = private_key.public_key()

# Serialize public key
public_pem = public_key.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode()

# Serialize private key
private_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
).decode()
```

### Partial File Encryption

```python
from xiaoshiai_hub import upload_folder
from xiaoshiai_hub.encryption import EncryptionAlgorithm

# Upload folder with partial encryption
commit_hash = upload_folder(
    folder_path="./my_model",
    repo_id="demo/my-model",
    encryption_key="your-secret-key",
    encryption_algorithm=EncryptionAlgorithm.AES_256_CBC,
    encryption_exclude=["README.md", "*.yaml"],  # Don't encrypt these files
    username="your-username",
    password="your-password",
)
```

## ⚙️ Configuration

### Environment Variables

```bash
# Hub endpoint
export MOHA_ENDPOINT="https://your-hub-url.com/moha"

# Authentication
export MOHA_USERNAME="your-username"
export MOHA_PASSWORD="your-password"

# Encryption keys (optional)
export ENCRYPTION_KEY="your-32-character-encryption-key"
export DECRYPTION_KEY="your-32-character-decryption-key"
```

### Using .env File

Create a `.env` file:

```bash
MOHA_ENDPOINT=https://your-hub-url.com/moha
MOHA_USERNAME=your-username
MOHA_PASSWORD=your-password
ENCRYPTION_KEY=your-encryption-key
```

Then load it in your code:

```python
from dotenv import load_dotenv
load_dotenv()

from xiaoshiai_hub import moha_hub_download

# Automatically uses credentials from environment variables
file_path = moha_hub_download(
    repo_id="demo/demo",
    filename="config.yaml",
)
```

## 📚 Examples

The project includes comprehensive examples in the `examples/` directory:

- **01_basic_usage.py** - Basic usage examples
- **02_download_file.py** - File download examples
- **03_download_repository.py** - Repository download examples
- **04_upload_file.py** - File upload examples
- **05_upload_folder.py** - Folder upload examples
- **06_encryption.py** - Encryption examples
- **07_complete_workflow.py** - Complete workflow example

Run examples:

```bash
# Set environment variables
export MOHA_USERNAME="your-username"
export MOHA_PASSWORD="your-password"

# Run examples
python examples/01_basic_usage.py
python examples/07_complete_workflow.py
```

See [examples/README.md](examples/README.md) for details.

## 🧪 Testing

Run tests:

```bash
# Install development dependencies
pip install xiaoshiai-hub[dev]

# Run all tests
pytest

# Run specific test file
pytest tests/test_client.py

# Run tests with coverage
pytest --cov=xiaoshiai_hub --cov-report=html

# Run tests with verbose output
pytest -v
```


