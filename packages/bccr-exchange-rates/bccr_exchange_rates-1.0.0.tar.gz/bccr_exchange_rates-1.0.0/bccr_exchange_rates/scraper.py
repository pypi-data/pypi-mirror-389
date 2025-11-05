"""
HTML scraper for BCCR Tipo de Cambio Ventanilla page.

Scrapes the live HTML page to get the current list of entities
that are actually reporting exchange rates today.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Any, Optional
import re

VENTANILLA_URL = "https://gee.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmConsultaTCVentanilla.aspx"


def scrape_ventanilla_page(date: Optional[str] = None) -> Dict[str, Any]:
    """
    Scrape the BCCR ventanilla page to get current exchange rate entities.

    Args:
        date: Optional date in YYYY-MM-DD format (defaults to today)

    Returns:
        Dictionary with:
        - date: str (date of the data)
        - entities: List[Dict] (list of all entities with their rates)
        - metadata: Dict (page metadata)

    Raises:
        requests.RequestException: If page fetch fails
        ValueError: If parsing fails
    """
    try:
        # If a specific date is provided, use postback method
        if date:
            return fetch_ventanilla_for_specific_date(date)

        # Otherwise, fetch today's data (simple GET)
        response = requests.get(VENTANILLA_URL, timeout=30)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract the date from the page
        page_date = extract_page_date(soup)

        # Find and parse the exchange rate table
        entities = parse_exchange_rate_table(soup)

        return {
            'date': page_date,
            'entities': entities,
            'metadata': {
                'source_url': VENTANILLA_URL,
                'source_type': 'html_scraping',
                'scrape_timestamp': datetime.now().isoformat(),
                'total_entities': len(entities),
                'date_requested': date or 'today'
            }
        }

    except Exception as e:
        raise ValueError(f"Failed to scrape ventanilla page: {e}")


def fetch_ventanilla_for_specific_date(target_date: str) -> Dict[str, Any]:
    """
    Fetch ventanilla page for a specific date using calendar interaction.

    The BCCR page requires a multi-step ASP.NET WebForms process:
    1. GET initial page to extract ViewState + EventValidation
    2. POST to open calendar (click imgCalendario image)
    3. POST to navigate month-by-month to target month:
       - Extract "previous month" link dynamically from calendar HTML
       - Navigate one month at a time using V-prefixed event arguments
       - Repeat until reaching target month
    4. POST to select specific date (Calendar1 with day argument, no V prefix)
    5. Parse the response HTML

    The V prefix is used for month navigation in ASP.NET Calendar controls.
    Navigation must be iterative because direct jumps to distant months fail.

    Args:
        target_date: Date in YYYY-MM-DD format

    Returns:
        Dictionary with date, entities, and metadata

    Raises:
        requests.RequestException: If page fetch fails
        ValueError: If date format is invalid or parsing fails
    """
    try:
        # Calculate the calendar day argument (days since Jan 1, 2000)
        from .utils import date_to_calendar_days, parse_spanish_date, format_last_update
        from datetime import datetime as dt

        date_obj = dt.strptime(target_date, '%Y-%m-%d').date()
        calendar_days = date_to_calendar_days(date_obj)

        # Determine if we need month navigation (compare with current date)
        today = dt.now().date()
        needs_navigation = (date_obj.year != today.year) or (date_obj.month != today.month)

        # Calculate how many months to navigate back
        months_diff = (today.year - date_obj.year) * 12 + (today.month - date_obj.month)

        # Create a session to maintain cookies
        session = requests.Session()

        # Step 1: GET initial page to extract ViewState
        print(f"[Step 1] Fetching initial page...")
        response = session.get(VENTANILLA_URL, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract initial ViewState and EventValidation
        viewstate = soup.find('input', {'name': '__VIEWSTATE'})
        eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})
        viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})

        if not viewstate or not eventvalidation:
            raise ValueError("Could not find ViewState or EventValidation in initial page")

        # Step 2: Click calendar image to open/initialize calendar
        print(f"[Step 2] Opening calendar control...")

        form_data_step1 = {
            '__EVENTTARGET': '',
            '__EVENTARGUMENT': '',
            '__VIEWSTATE': viewstate['value'],
            '__VIEWSTATEGENERATOR': viewstate_generator['value'] if viewstate_generator else '',
            '__EVENTVALIDATION': eventvalidation['value'],
            'imgCalendario.x': '10',
            'imgCalendario.y': '10',
            'CtrlBuscar2:txtPalabras': ''
        }

        response = session.post(VENTANILLA_URL, data=form_data_step1, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract fresh ViewState and EventValidation after opening calendar
        viewstate = soup.find('input', {'name': '__VIEWSTATE'})
        eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})
        viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})

        if not viewstate or not eventvalidation:
            raise ValueError("Could not find ViewState or EventValidation after opening calendar")

        # Step 3: Navigate to target month iteratively (month-by-month)
        if needs_navigation:
            print(f"[Step 3] Need to navigate {months_diff} month(s) back to {date_obj.strftime('%B %Y')}...")

            # Navigate month-by-month using dynamically extracted prev links
            for i in range(months_diff):
                # Extract the current "previous month" link
                prev_link = extract_prev_month_link(soup)

                if not prev_link:
                    raise ValueError(f"Could not find 'previous month' link at navigation step {i+1}")

                print(f"  [Step 3.{i+1}] Navigating to previous month ({prev_link})...")

                form_data_navigate = {
                    '__EVENTTARGET': 'Calendar1',
                    '__EVENTARGUMENT': prev_link,  # Use dynamically extracted link
                    '__VIEWSTATE': viewstate['value'],
                    '__VIEWSTATEGENERATOR': viewstate_generator['value'] if viewstate_generator else '',
                    '__EVENTVALIDATION': eventvalidation['value'],
                    'CtrlBuscar2:txtPalabras': ''
                }

                response = session.post(VENTANILLA_URL, data=form_data_navigate, timeout=30)
                response.raise_for_status()

                soup = BeautifulSoup(response.content, 'html.parser')

                # Extract fresh ViewState for next iteration
                viewstate = soup.find('input', {'name': '__VIEWSTATE'})
                eventvalidation = soup.find('input', {'name': '__EVENTVALIDATION'})
                viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})

            print(f"  [Step 3] Successfully navigated to {date_obj.strftime('%B %Y')}")
        else:
            print(f"[Step 3] Skipping month navigation (target is current month)")

        # Step 4: Select specific date using Calendar1 control (without V prefix)
        print(f"[Step 4] Selecting date {target_date} (day {calendar_days})...")

        form_data_select = {
            '__EVENTTARGET': 'Calendar1',
            '__EVENTARGUMENT': str(calendar_days),  # No V prefix for day selection
            '__VIEWSTATE': viewstate['value'],
            '__VIEWSTATEGENERATOR': viewstate_generator['value'] if viewstate_generator else '',
            '__EVENTVALIDATION': eventvalidation['value'],
            'CtrlBuscar2:txtPalabras': ''
        }

        response = session.post(VENTANILLA_URL, data=form_data_select, timeout=30)
        response.raise_for_status()

        print(f"Date selection successful (status: {response.status_code})")

        # Step 5: Parse response HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract the date from the page (should match target_date)
        page_date = extract_page_date(soup)

        # Find and parse the exchange rate table
        entities = parse_exchange_rate_table(soup)

        print(f"Successfully scraped {len(entities)} entities for date {page_date}")

        return {
            'date': page_date,
            'entities': entities,
            'metadata': {
                'source_url': VENTANILLA_URL,
                'source_type': 'html_scraping_calendar_iterative',
                'scrape_timestamp': datetime.now().isoformat(),
                'total_entities': len(entities),
                'date_requested': target_date,
                'date_retrieved': page_date,
                'calendar_days_argument': calendar_days,
                'month_navigation_required': needs_navigation,
                'months_navigated': months_diff if needs_navigation else 0
            }
        }

    except Exception as e:
        raise ValueError(f"Failed to fetch ventanilla page for date {target_date}: {e}")


def extract_prev_month_link(soup: BeautifulSoup) -> Optional[str]:
    """
    Extract the 'previous month' navigation link from the calendar.

    Args:
        soup: BeautifulSoup object with Calendar1 control

    Returns:
        Event argument for previous month navigation, or None if not found
    """
    calendar = soup.find('table', id='Calendar1')
    if not calendar:
        return None

    # Find all links in the calendar
    links = calendar.find_all('a')

    for link in links:
        title = link.get('title', '').lower()
        # Look for "previous month" or Spanish "mes anterior"
        if 'previous month' in title or 'anterior' in title:
            href = link.get('href', '')
            # Extract __EVENTARGUMENT from javascript:__doPostBack('Calendar1','V9405')
            match = re.search(r"__doPostBack\('([^']*)',\s*'([^']*)'\)", href)
            if match:
                return match.group(2)  # Return the event argument (e.g., "V9405")

    return None


def extract_page_date(soup: BeautifulSoup) -> str:
    """
    Extract the date from the page header.

    The page typically shows: "lunes, 4 de noviembre de 2025"

    Args:
        soup: BeautifulSoup object

    Returns:
        Date string in ISO format (YYYY-MM-DD)
    """
    # Look for the date in common locations
    # Try finding by ID or class (inspect the actual page to find the right selector)

    # Strategy 1: Look for span/div with date-like text
    date_candidates = soup.find_all(string=re.compile(r'\d+ de \w+ de \d{4}'))

    if date_candidates:
        date_text = date_candidates[0].strip()
        # Parse Spanish date
        from .utils import parse_spanish_date
        return parse_spanish_date(date_text)

    # Strategy 2: Look for any text containing a date pattern
    page_text = soup.get_text()
    date_match = re.search(r'(\w+,\s+\d+\s+de\s+\w+\s+de\s+\d{4})', page_text)

    if date_match:
        from .utils import parse_spanish_date
        return parse_spanish_date(date_match.group(1))

    # Fallback to today
    return datetime.now().strftime('%Y-%m-%d')


def parse_exchange_rate_table(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """
    Parse the exchange rate table from the page.

    The table has ID="DG" and structure:
    | Tipo de Entidad | Entidad Autorizada | Compra | Venta | Diferencial | Última Actualización |

    Args:
        soup: BeautifulSoup object

    Returns:
        List of entity dictionaries
    """
    entities = []

    # The exchange rate table has ID="DG"
    table = soup.find('table', id='DG')

    if not table:
        # Fallback: try to find by headers
        tables = soup.find_all('table')
        for t in tables:
            headers = t.find_all('th')
            header_text = ' '.join([h.get_text().strip() for h in headers])
            if 'Compra' in header_text and 'Venta' in header_text and 'Entidad' in header_text:
                table = t
                break

    if not table:
        raise ValueError("Could not find exchange rate table (ID=DG) on page")

    # Parse table rows
    rows = table.find_all('tr')

    # Skip header row(s)
    data_rows = [r for r in rows if r.find('td')]

    current_entity_type = None

    for row in data_rows:
        cols = row.find_all('td')

        if len(cols) < 6:
            continue

        try:
            # Extract data from columns
            # Column structure might vary - inspect actual page
            entity_type_cell = cols[0].get_text().strip()
            entity_name = cols[1].get_text().strip()
            buy_rate_str = cols[2].get_text().strip()
            sell_rate_str = cols[3].get_text().strip()
            spread_str = cols[4].get_text().strip()
            last_update_str = cols[5].get_text().strip()

            # Handle entity type (might be colspan/rowspan in some rows)
            if entity_type_cell:
                current_entity_type = entity_type_cell
            else:
                # Use the last known entity type if cell is empty (rowspan case)
                entity_type_cell = current_entity_type or "Unknown"

            # Parse numeric values
            buy_rate = parse_rate(buy_rate_str)
            sell_rate = parse_rate(sell_rate_str)
            spread = parse_rate(spread_str)

            # Parse timestamp
            last_update = parse_last_update(last_update_str)

            entity = {
                'entity_type': entity_type_cell,
                'entity_name': entity_name,
                'buy_rate': buy_rate,
                'sell_rate': sell_rate,
                'spread': spread,
                'last_update': last_update,
                'last_update_str': last_update_str
            }

            entities.append(entity)

        except Exception as e:
            # Skip rows that fail to parse
            print(f"Warning: Failed to parse row: {e}")
            continue

    return entities


def parse_rate(rate_str: str) -> Optional[float]:
    """
    Parse a rate string to float.

    Handles formats like: "495.00", "495,00", "-", "N/D"

    Args:
        rate_str: Rate string

    Returns:
        Float value or None if not available
    """
    if not rate_str or rate_str.strip() in ['-', 'N/D', 'n/d', '']:
        return None

    # Remove any non-numeric characters except . and ,
    cleaned = re.sub(r'[^\d.,]', '', rate_str)

    # Replace comma with period (European format)
    cleaned = cleaned.replace(',', '.')

    try:
        return float(cleaned)
    except ValueError:
        return None


def parse_last_update(timestamp_str: str) -> Optional[str]:
    """
    Parse last update timestamp.

    Formats: "04/11/2025 10:30 a.m.", "04/11/2025 02:45 p.m."

    Args:
        timestamp_str: Timestamp string

    Returns:
        ISO format timestamp or None
    """
    if not timestamp_str or timestamp_str.strip() in ['-', 'N/D']:
        return None

    try:
        from .utils import format_last_update
        dt = format_last_update(timestamp_str)
        return dt.isoformat()
    except Exception:
        # Return as-is if parsing fails
        return timestamp_str


def group_entities_by_type(entities: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group entities by their entity_type.

    Args:
        entities: List of entity dictionaries

    Returns:
        Dictionary mapping entity_type to list of entities
    """
    grouped = {}

    for entity in entities:
        entity_type = entity['entity_type']

        if entity_type not in grouped:
            grouped[entity_type] = []

        grouped[entity_type].append(entity)

    return grouped


def get_entity_summary(entities: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Get summary statistics about the entities.

    Args:
        entities: List of entity dictionaries

    Returns:
        Summary dictionary
    """
    grouped = group_entities_by_type(entities)

    categories = []
    for entity_type, type_entities in grouped.items():
        # Count how many have data
        with_buy = sum(1 for e in type_entities if e['buy_rate'] is not None)
        with_sell = sum(1 for e in type_entities if e['sell_rate'] is not None)

        categories.append({
            'entity_type': entity_type,
            'total_entities': len(type_entities),
            'entities_with_buy_rate': with_buy,
            'entities_with_sell_rate': with_sell
        })

    return {
        'total_entities': len(entities),
        'total_categories': len(grouped),
        'categories': categories
    }
