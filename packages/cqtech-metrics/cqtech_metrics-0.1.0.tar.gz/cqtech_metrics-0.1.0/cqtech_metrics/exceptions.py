"""Custom exceptions for CQTech Metrics SDK"""


class CQTechException(Exception):
    """Base exception for CQTech Metrics SDK"""
    pass


class AuthenticationError(CQTechException):
    """Raised when authentication fails"""
    pass


class APIError(CQTechException):
    """Raised when API returns an error"""
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
        super().__init__(f"API Error {code}: {message}")


class RequestError(CQTechException):
    """Raised when request fails"""
    pass


class ValidationError(CQTechException):
    """Raised when validation fails"""
    pass