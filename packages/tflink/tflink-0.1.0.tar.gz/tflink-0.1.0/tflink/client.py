"""
Main client for tflink file upload service
"""

import os
from pathlib import Path
from typing import Optional, Union

import requests

from tflink.models import UploadResult
from tflink.exceptions import (
    UploadError,
    AuthenticationError,
    FileNotFoundError,
    NetworkError,
)


class TFLinkClient:
    """
    Client for uploading files to tmpfile.link

    Args:
        user_id: Optional user ID for authenticated uploads
        auth_token: Optional authentication token for authenticated uploads
        base_url: API base URL (default: https://tmpfile.link)
        timeout: Request timeout in seconds (default: 300)

    Example:
        # Anonymous upload
        client = TFLinkClient()
        result = client.upload('document.pdf')
        print(result.download_link)

        # Authenticated upload
        client = TFLinkClient(user_id='your_user_id', auth_token='your_token')
        result = client.upload('document.pdf')
        print(result.download_link)
    """

    def __init__(
        self,
        user_id: Optional[str] = None,
        auth_token: Optional[str] = None,
        base_url: str = "https://tmpfile.link",
        timeout: int = 300
    ):
        """Initialize the TFLink client"""
        self.user_id = user_id
        self.auth_token = auth_token
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.upload_url = f"{self.base_url}/api/upload"

        # Validate authentication parameters
        if (user_id and not auth_token) or (auth_token and not user_id):
            raise ValueError("Both user_id and auth_token must be provided for authenticated uploads")

    def upload(
        self,
        file_path: Union[str, Path],
        filename: Optional[str] = None
    ) -> UploadResult:
        """
        Upload a file to tmpfile.link

        Args:
            file_path: Path to the file to upload
            filename: Optional custom filename (default: use original filename)

        Returns:
            UploadResult object containing download link and metadata

        Raises:
            FileNotFoundError: If the file does not exist
            UploadError: If the upload fails
            AuthenticationError: If authentication fails
            NetworkError: If network request fails

        Example:
            result = client.upload('/path/to/file.pdf')
            print(f"Download link: {result.download_link}")
            print(f"File size: {result.size} bytes")
        """
        # Convert to Path object
        file_path = Path(file_path)

        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise FileNotFoundError(f"Path is not a file: {file_path}")

        # Use custom filename or original filename
        upload_filename = filename or file_path.name

        # Prepare headers
        headers = {}
        if self.user_id and self.auth_token:
            headers['X-User-Id'] = self.user_id
            headers['X-Auth-Token'] = self.auth_token

        # Prepare file for upload
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (upload_filename, f)}

                # Make the upload request
                response = requests.post(
                    self.upload_url,
                    headers=headers,
                    files=files,
                    timeout=self.timeout
                )

        except requests.exceptions.Timeout:
            raise NetworkError(f"Upload timeout after {self.timeout} seconds")
        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Connection error: {str(e)}")
        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Request failed: {str(e)}")
        except OSError as e:
            raise FileNotFoundError(f"Failed to read file: {str(e)}")

        # Handle response
        return self._handle_response(response)

    def _handle_response(self, response: requests.Response) -> UploadResult:
        """
        Handle the API response

        Args:
            response: Response object from requests

        Returns:
            UploadResult object

        Raises:
            AuthenticationError: If authentication fails (401)
            UploadError: If upload fails
        """
        # Check for authentication errors
        if response.status_code == 401:
            raise AuthenticationError(
                "Authentication failed. Please check your user_id and auth_token."
            )

        # Check for other HTTP errors
        if response.status_code == 403:
            raise AuthenticationError(
                "Access forbidden. Please check your credentials."
            )

        if response.status_code == 413:
            raise UploadError(
                "File too large. Please check the file size limits."
            )

        if response.status_code >= 500:
            raise UploadError(
                f"Server error ({response.status_code}). Please try again later."
            )

        if not response.ok:
            try:
                error_data = response.json()
                error_message = error_data.get('error', response.text)
            except Exception:
                error_message = response.text

            raise UploadError(
                f"Upload failed with status {response.status_code}: {error_message}"
            )

        # Parse successful response
        try:
            data = response.json()
        except ValueError as e:
            raise UploadError(f"Failed to parse response: {str(e)}")

        # Validate response structure
        required_fields = ['fileName', 'downloadLink', 'downloadLinkEncoded', 'size', 'type', 'uploadedTo']
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            raise UploadError(
                f"Invalid response structure. Missing fields: {', '.join(missing_fields)}"
            )

        # Create and return UploadResult
        try:
            return UploadResult.from_json(data)
        except Exception as e:
            raise UploadError(f"Failed to create UploadResult: {str(e)}")

    def is_authenticated(self) -> bool:
        """Check if the client is configured for authenticated uploads"""
        return bool(self.user_id and self.auth_token)

    def __repr__(self) -> str:
        """String representation of the client"""
        auth_status = "authenticated" if self.is_authenticated() else "anonymous"
        return f"TFLinkClient(base_url='{self.base_url}', mode='{auth_status}')"
