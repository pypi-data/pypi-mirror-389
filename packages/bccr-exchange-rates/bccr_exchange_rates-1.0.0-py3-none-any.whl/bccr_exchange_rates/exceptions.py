"""
Custom exceptions for bccr-exchange-rates library.
"""


class BCCRError(Exception):
    """Base exception for all BCCR-related errors."""
    pass


class BCCRScrapingError(BCCRError):
    """Raised when scraping the BCCR ventanilla page fails."""
    pass


class BCCRDateError(BCCRError):
    """Raised when date validation or parsing fails."""
    pass


class BCCRConnectionError(BCCRError):
    """Raised when connection to BCCR website fails."""
    pass


class BCCRParseError(BCCRError):
    """Raised when parsing HTML response fails."""
    pass
