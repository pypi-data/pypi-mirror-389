"""
Data models for tflink
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class UploadResult:
    """
    Represents the result of a file upload

    Attributes:
        file_name: Original file name
        download_link: Direct download URL (unencoded, human-readable)
            Example: "https://d.tmpfile.link/public/2025-07-31/uuid/file.png"
            Use this for: displaying to users, clickable links in web browsers
        download_link_encoded: URL-encoded download link (safe for all contexts)
            Example: "https://d.tmpfile.link/public%2F2025-07-31%2Fuuid%2Ffile.png"
            Use this for: programmatic access, API calls, special characters in filenames
        size: File size in bytes
        file_type: MIME type of the file
        uploaded_to: Upload destination (e.g., "public" or "user: USER_ID")

    Note:
        Both links point to the same file. The difference is in encoding:
        - download_link: Contains forward slashes (/) in the path
        - download_link_encoded: Has forward slashes encoded as %2F

        Most users should use download_link for simplicity. Use download_link_encoded
        when you need to ensure the URL is properly encoded for all contexts.
    """
    file_name: str
    download_link: str
    download_link_encoded: str
    size: int
    file_type: str
    uploaded_to: str

    @classmethod
    def from_json(cls, data: dict) -> 'UploadResult':
        """
        Create UploadResult from JSON response

        Args:
            data: JSON response from the API

        Returns:
            UploadResult instance
        """
        return cls(
            file_name=data['fileName'],
            download_link=data['downloadLink'],
            download_link_encoded=data['downloadLinkEncoded'],
            size=data['size'],
            file_type=data['type'],
            uploaded_to=data['uploadedTo']
        )

    def __str__(self) -> str:
        """String representation showing the download link"""
        return f"UploadResult(file_name='{self.file_name}', download_link='{self.download_link}')"

    def __repr__(self) -> str:
        """Detailed representation"""
        return (
            f"UploadResult(file_name='{self.file_name}', "
            f"download_link='{self.download_link}', "
            f"size={self.size}, "
            f"file_type='{self.file_type}')"
        )
