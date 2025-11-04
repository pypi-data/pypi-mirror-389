"""
Custom exceptions for the GM SDK.
"""


class GMError(Exception):
    """Base exception for GM SDK errors."""
    pass


class ConnectionError(GMError):
    """Connection-related errors."""
    pass


class TimeoutError(GMError):
    """Timeout-related errors."""
    pass


class AuthenticationError(GMError):
    """Authentication-related errors."""
    pass


class QueryError(GMError):
    """Query-related errors."""
    pass


class DataNotFoundError(GMError):
    """Data not found errors."""
    pass


class SerializationError(GMError):
    """Serialization-related errors."""
    pass


class ConfigurationError(GMError):
    """Configuration-related errors."""
    pass


class ServerError(GMError):
    """Server-side errors."""
    pass