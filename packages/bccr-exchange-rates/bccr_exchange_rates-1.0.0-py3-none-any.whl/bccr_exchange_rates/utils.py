"""
Date parsing utilities for BCCR date formats.

Handles Spanish date formats used by BCCR:
- "lunes, 4 de noviembre de 2025" (Spanish long format)
- "04/11/2025 10:30 a.m." (timestamp format)
- "DD/MM/YYYY" (BCCR input format)
"""

from datetime import datetime, date, timedelta
import re
from typing import Union


# Spanish month names to numbers
SPANISH_MONTHS = {
    'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
    'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
    'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12
}


def parse_spanish_date(date_str: str) -> str:
    """
    Parse a Spanish date string to ISO format (YYYY-MM-DD).

    Handles formats like:
    - "lunes, 4 de noviembre de 2025"
    - "4 de noviembre de 2025"

    Args:
        date_str: Spanish date string

    Returns:
        Date in ISO format (YYYY-MM-DD)

    Raises:
        ValueError: If date string cannot be parsed
    """
    # Remove day of week if present (e.g., "lunes, ")
    date_str = re.sub(r'^\w+,\s*', '', date_str.strip())

    # Pattern: "4 de noviembre de 2025"
    pattern = r'(\d+)\s+de\s+(\w+)\s+de\s+(\d{4})'
    match = re.search(pattern, date_str)

    if not match:
        raise ValueError(f"Cannot parse Spanish date: {date_str}")

    day = int(match.group(1))
    month_name = match.group(2).lower()
    year = int(match.group(3))

    month = SPANISH_MONTHS.get(month_name)
    if not month:
        raise ValueError(f"Unknown Spanish month: {month_name}")

    # Create date object and return ISO format
    date_obj = date(year, month, day)
    return date_obj.strftime('%Y-%m-%d')


def format_spanish_date(date_obj: Union[date, datetime]) -> str:
    """
    Format a date object to BCCR format (DD/MM/YYYY).

    Args:
        date_obj: Date or datetime object

    Returns:
        Date string in DD/MM/YYYY format

    Example:
        >>> format_spanish_date(date(2025, 11, 4))
        '04/11/2025'
    """
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()

    return date_obj.strftime('%d/%m/%Y')


def format_last_update(timestamp_str: str) -> datetime:
    """
    Parse BCCR last update timestamp to datetime object.

    Handles formats like:
    - "04/11/2025 10:30 a.m."
    - "04/11/2025 02:45 p.m."

    Args:
        timestamp_str: Timestamp string from BCCR

    Returns:
        datetime object

    Raises:
        ValueError: If timestamp cannot be parsed
    """
    # Clean the string
    timestamp_str = timestamp_str.strip()

    # Replace Spanish period markers
    timestamp_str = timestamp_str.replace('a.m.', 'AM').replace('p.m.', 'PM')
    timestamp_str = timestamp_str.replace('a. m.', 'AM').replace('p. m.', 'PM')

    # Try to parse with AM/PM
    try:
        return datetime.strptime(timestamp_str, '%d/%m/%Y %I:%M %p')
    except ValueError:
        pass

    # Try without AM/PM (24-hour format)
    try:
        return datetime.strptime(timestamp_str, '%d/%m/%Y %H:%M')
    except ValueError:
        pass

    # Try date only
    try:
        dt = datetime.strptime(timestamp_str, '%d/%m/%Y')
        return dt
    except ValueError:
        raise ValueError(f"Cannot parse timestamp: {timestamp_str}")


def validate_date_range(date_str: str, max_days_back: int = 365) -> bool:
    """
    Validate that a date is within an acceptable range.

    Args:
        date_str: Date string in YYYY-MM-DD format
        max_days_back: Maximum days in the past allowed

    Returns:
        True if valid, False otherwise
    """
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        today = date.today()

        # Check if date is in the future
        if target_date > today:
            return False

        # Check if date is too far in the past
        days_diff = (today - target_date).days
        if days_diff > max_days_back:
            return False

        return True

    except ValueError:
        return False


def date_to_calendar_days(target_date: Union[date, str]) -> int:
    """
    Convert a date to the number of days since the BCCR calendar epoch.

    The BCCR website uses an ASP.NET Calendar control with an epoch of
    January 1, 2000. The __EVENTARGUMENT parameter expects the number
    of days since this epoch.

    Args:
        target_date: Date object or string in YYYY-MM-DD format

    Returns:
        Number of days since January 1, 2000

    Example:
        >>> date_to_calendar_days('2025-11-01')
        9436
        >>> date_to_calendar_days('2025-11-02')
        9437
    """
    # BCCR Calendar epoch (ASP.NET default)
    epoch = date(2000, 1, 1)

    # Convert string to date if needed
    if isinstance(target_date, str):
        target_date = datetime.strptime(target_date, '%Y-%m-%d').date()

    # Calculate days since epoch
    days_since_epoch = (target_date - epoch).days

    return days_since_epoch


def validate_date_parameter(date_str: str, max_days_back: int = 365) -> tuple[bool, str]:
    """
    Validate a date parameter for exchange rate queries.

    Checks:
    - Date format is valid (YYYY-MM-DD)
    - Date is not in the future
    - Date is not too far in the past (configurable)

    Args:
        date_str: Date string in YYYY-MM-DD format
        max_days_back: Maximum number of days in the past allowed (default: 365)

    Returns:
        Tuple of (is_valid, error_message)
        - If valid: (True, "")
        - If invalid: (False, "descriptive error message")

    Example:
        >>> validate_date_parameter('2025-11-05')
        (True, '')
        >>> validate_date_parameter('2026-01-01')
        (False, 'Date cannot be in the future. Please provide a date up to today.')
    """
    # Check format
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return (False, f"Invalid date format: '{date_str}'. Expected format: YYYY-MM-DD (e.g., 2025-11-05)")

    today = date.today()

    # Check if date is in the future
    if target_date > today:
        return (False, f"Date cannot be in the future. Please provide a date up to today ({today.strftime('%Y-%m-%d')}).")

    # Check if date is too far in the past
    days_diff = (today - target_date).days
    if days_diff > max_days_back:
        oldest_allowed = (today - timedelta(days=max_days_back)).strftime('%Y-%m-%d')
        return (False, f"Date is too far in the past. Maximum {max_days_back} days back allowed. Oldest date: {oldest_allowed}")

    return (True, "")
