"""
Custom exceptions for tflink
"""


class TFLinkError(Exception):
    """Base exception for all tflink errors"""
    pass


class UploadError(TFLinkError):
    """Raised when file upload fails"""
    pass


class AuthenticationError(TFLinkError):
    """Raised when authentication fails"""
    pass


class FileNotFoundError(TFLinkError):
    """Raised when the specified file does not exist"""
    pass


class NetworkError(TFLinkError):
    """Raised when network request fails"""
    pass
