"""
tflink - A Python client for tmpfile.link file upload service

This library provides a simple interface to upload files to tmpfile.link
and retrieve download links.

Basic usage:
    from tflink import TFLinkClient

    # Anonymous upload
    client = TFLinkClient()
    result = client.upload('path/to/file.pdf')
    print(result.download_link)

    # Authenticated upload
    client = TFLinkClient(user_id='YOUR_USER_ID', auth_token='YOUR_AUTH_TOKEN')
    result = client.upload('path/to/file.pdf')
    print(result.download_link)
"""

__version__ = '0.1.1'
__author__ = 'tfLink'
__license__ = 'MIT'

from tflink.client import TFLinkClient
from tflink.models import UploadResult
from tflink.exceptions import (
    TFLinkError,
    UploadError,
    AuthenticationError,
    FileNotFoundError,
)

__all__ = [
    'TFLinkClient',
    'UploadResult',
    'TFLinkError',
    'UploadError',
    'AuthenticationError',
    'FileNotFoundError',
]
