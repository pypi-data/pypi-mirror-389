"""
XiaoShi AI Hub Python SDK

A Python library for interacting with XiaoShi AI Hub repositories.
"""

from .client import HubClient, DEFAULT_BASE_URL
from .download import (
    moha_hub_download,
    snapshot_download,
)
from .exceptions import (
    HubException,
    RepositoryNotFoundError,
    FileNotFoundError,
    AuthenticationError,
    EncryptionError,
)
from .types import (
    Repository,
    Ref,
    GitContent,
    Commit,
)

# Upload functionality (requires GitPython)
try:
    from .upload import (
        upload_file,
        upload_folder,
        UploadError,
    )
    _upload_available = True
except ImportError:
    _upload_available = False
    upload_file = None
    upload_folder = None
    UploadError = None

# Encryption functionality
try:
    from .encryption import (
        EncryptionAlgorithm,
        encrypt_file,
        decrypt_file,
    )
    _encryption_available = True
except ImportError:
    _encryption_available = False
    EncryptionAlgorithm = None
    encrypt_file = None
    decrypt_file = None

__version__ = "0.1.0"

__all__ = [
    # Client
    "HubClient",
    "DEFAULT_BASE_URL",
    # Download
    "moha_hub_download",
    "snapshot_download",
    # Upload
    "upload_file",
    "upload_folder",
    # Exceptions
    "HubException",
    "RepositoryNotFoundError",
    "FileNotFoundError",
    "AuthenticationError",
    "EncryptionError",
    "UploadError",
    # Types
    "Repository",
    "Ref",
    "GitContent",
    "Commit",
    # Encryption
    "EncryptionAlgorithm",
    "encrypt_file",
    "decrypt_file",
]

