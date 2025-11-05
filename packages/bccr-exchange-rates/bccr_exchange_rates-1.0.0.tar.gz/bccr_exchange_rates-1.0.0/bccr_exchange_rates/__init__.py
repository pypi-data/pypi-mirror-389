"""
bccr-exchange-rates: Python library for scraping Costa Rican exchange rates from BCCR.

This library provides a simple interface to scrape real-time and historical
exchange rate data from the Banco Central de Costa Rica (BCCR) ventanilla page.

Basic usage:
    >>> from bccr_exchange_rates import get_current_rates, search_entities
    >>>
    >>> # Get current rates
    >>> rates = get_current_rates()
    >>> print(f"Found {len(rates)} entities")
    >>>
    >>> # Get rates for a specific date
    >>> rates = get_rates_by_date("2025-11-01")
    >>>
    >>> # Search for specific entity
    >>> multimoney = search_entities("MultiMoney")
"""

__version__ = "0.1.0"
__author__ = "Mauricio Loría"
__license__ = "MIT"

from .scraper import (
    scrape_ventanilla_page,
    group_entities_by_type,
    get_entity_summary,
    VENTANILLA_URL
)
from .utils import (
    parse_spanish_date,
    format_spanish_date,
    format_last_update,
    validate_date_parameter,
    date_to_calendar_days
)
from .exceptions import (
    BCCRError,
    BCCRScrapingError,
    BCCRDateError,
    BCCRConnectionError,
    BCCRParseError
)

# Public API


def get_current_rates(format="flat"):
    """
    Get current exchange rates from all entities.

    Args:
        format: Response format - "flat" (list) or "hierarchical" (grouped by type)

    Returns:
        List of entity dictionaries if format="flat",
        Dictionary mapping entity types to entities if format="hierarchical"

    Raises:
        BCCRScrapingError: If scraping fails
        BCCRConnectionError: If connection to BCCR website fails

    Example:
        >>> rates = get_current_rates()
        >>> for entity in rates:
        ...     print(f"{entity['entity_name']}: Buy {entity['buy_rate']}, Sell {entity['sell_rate']}")
    """
    try:
        result = scrape_ventanilla_page()
        entities = result['entities']

        # Filter out header rows (entities with no rates)
        entities = [e for e in entities if e['buy_rate'] is not None or e['sell_rate'] is not None]

        if format == "hierarchical":
            return group_entities_by_type(entities)

        return entities
    except ValueError as e:
        raise BCCRScrapingError(f"Failed to scrape current rates: {e}")
    except Exception as e:
        raise BCCRConnectionError(f"Failed to connect to BCCR: {e}")


def get_rates_by_date(date, format="flat"):
    """
    Get exchange rates for a specific date.

    Args:
        date: Date in YYYY-MM-DD format (e.g., "2025-11-01")
        format: Response format - "flat" (list) or "hierarchical" (grouped by type)

    Returns:
        List of entity dictionaries if format="flat",
        Dictionary mapping entity types to entities if format="hierarchical"

    Raises:
        BCCRScrapingError: If scraping fails
        BCCRConnectionError: If connection to BCCR website fails
        BCCRDateError: If date is invalid

    Example:
        >>> rates = get_rates_by_date("2025-11-01")
        >>> print(f"Found {len(rates)} entities for 2025-11-01")
    """
    # Validate date
    is_valid, error_msg = validate_date_parameter(date)
    if not is_valid:
        raise BCCRDateError(error_msg)

    try:
        result = scrape_ventanilla_page(date=date)
        entities = result['entities']

        # Filter out header rows
        entities = [e for e in entities if e['buy_rate'] is not None or e['sell_rate'] is not None]

        if format == "hierarchical":
            return group_entities_by_type(entities)

        return entities
    except ValueError as e:
        raise BCCRScrapingError(f"Failed to scrape rates for {date}: {e}")
    except Exception as e:
        raise BCCRConnectionError(f"Failed to connect to BCCR: {e}")


def search_entities(query, date=None, format="flat"):
    """
    Search for entities by name or type.

    Args:
        query: Search term (searches both entity_name and entity_type)
        date: Optional date in YYYY-MM-DD format (defaults to today)
        format: Response format - "flat" (list) or "hierarchical" (grouped by type)

    Returns:
        List of matching entity dictionaries if format="flat",
        Dictionary mapping entity types to matching entities if format="hierarchical"

    Raises:
        BCCRScrapingError: If scraping fails
        BCCRConnectionError: If connection to BCCR website fails
        BCCRDateError: If date is invalid

    Example:
        >>> # Find all financial entities
        >>> financieras = search_entities("Financiera")
        >>>
        >>> # Find MultiMoney specifically
        >>> multimoney = search_entities("MultiMoney")
        >>> if multimoney:
        ...     print(f"MultiMoney buy rate: {multimoney[0]['buy_rate']}")
    """
    # Validate date if provided
    if date:
        is_valid, error_msg = validate_date_parameter(date)
        if not is_valid:
            raise BCCRDateError(error_msg)

    try:
        result = scrape_ventanilla_page(date=date)
        entities = result['entities']

        # Search for matching entities
        search_term = query.lower()
        matches = []

        for entity in entities:
            # Skip header rows
            if entity['buy_rate'] is None and entity['sell_rate'] is None:
                continue

            # Check if search term is in name or type
            if (search_term in entity['entity_name'].lower() or
                    search_term in entity['entity_type'].lower()):
                matches.append(entity)

        if format == "hierarchical":
            return group_entities_by_type(matches)

        return matches
    except ValueError as e:
        raise BCCRScrapingError(f"Failed to search entities: {e}")
    except Exception as e:
        raise BCCRConnectionError(f"Failed to connect to BCCR: {e}")


def get_entity_by_name(entity_name, date=None):
    """
    Get exchange rate for a specific entity by name (exact or partial match).

    Args:
        entity_name: Full or partial entity name (case-insensitive)
        date: Optional date in YYYY-MM-DD format (defaults to today)

    Returns:
        Entity dictionary if found, None otherwise

    Raises:
        BCCRScrapingError: If scraping fails
        BCCRConnectionError: If connection to BCCR website fails
        BCCRDateError: If date is invalid

    Example:
        >>> ari = get_entity_by_name("ARI")
        >>> if ari:
        ...     print(f"ARI rates - Buy: {ari['buy_rate']}, Sell: {ari['sell_rate']}")
    """
    matches = search_entities(entity_name, date=date, format="flat")
    return matches[0] if matches else None


# Export all public APIs
__all__ = [
    # Main API functions
    'get_current_rates',
    'get_rates_by_date',
    'search_entities',
    'get_entity_by_name',
    # Core functions (advanced usage)
    'scrape_ventanilla_page',
    'group_entities_by_type',
    'get_entity_summary',
    # Utilities
    'parse_spanish_date',
    'format_spanish_date',
    'validate_date_parameter',
    # Exceptions
    'BCCRError',
    'BCCRScrapingError',
    'BCCRDateError',
    'BCCRConnectionError',
    'BCCRParseError',
    # Constants
    'VENTANILLA_URL',
    # Metadata
    '__version__',
]
