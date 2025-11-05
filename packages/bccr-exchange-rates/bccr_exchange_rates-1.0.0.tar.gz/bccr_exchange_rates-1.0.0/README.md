# bccr-exchange-rates

[![PyPI version](https://badge.fury.io/py/bccr-exchange-rates.svg)](https://badge.fury.io/py/bccr-exchange-rates)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

Python library for scraping Costa Rican exchange rates from Banco Central de Costa Rica (BCCR).

Get real-time and historical exchange rate data from 39+ financial entities including banks, exchange houses, financial companies, cooperatives, and more.

## Features

- 🔄 **Real-time Data**: Get current exchange rates from all reporting entities
- 📅 **Historical Data**: Query rates for any past date
- 🔍 **Search & Filter**: Find specific entities by name or type
- 🏦 **Comprehensive Coverage**: 39+ entities across 7 categories
- 🚀 **Simple API**: Easy-to-use functions with sensible defaults
- ⚡ **No Authentication**: Direct HTML scraping, no API credentials needed
- 🐍 **Type-Safe**: Full type hints for better IDE support

## Installation

```bash
pip install bccr-exchange-rates
```

## Quick Start

```python
from bccr_exchange_rates import get_current_rates, search_entities

# Get current rates from all entities
rates = get_current_rates()
for entity in rates:
    print(f"{entity['entity_name']}: ₡{entity['buy_rate']} / ₡{entity['sell_rate']}")

# Search for a specific entity
multimoney = search_entities("MultiMoney")
if multimoney:
    rate = multimoney[0]
    print(f"MultiMoney - Buy: ₡{rate['buy_rate']}, Sell: ₡{rate['sell_rate']}")
```

## Usage Examples

### Get Current Rates

```python
from bccr_exchange_rates import get_current_rates

# Get all current rates as a flat list
rates = get_current_rates()
print(f"Found {len(rates)} entities with rates")

# Get rates grouped by entity type
rates_by_type = get_current_rates(format="hierarchical")
for entity_type, entities in rates_by_type.items():
    print(f"\n{entity_type}:")
    for entity in entities:
        print(f"  - {entity['entity_name']}: Buy ₡{entity['buy_rate']}, Sell ₡{entity['sell_rate']}")
```

### Get Historical Rates

```python
from bccr_exchange_rates import get_rates_by_date

# Get rates for a specific date
rates = get_rates_by_date("2025-11-01")
print(f"Rates for November 1, 2025: {len(rates)} entities")

# Get historical rates grouped by type
rates_by_type = get_rates_by_date("2025-10-15", format="hierarchical")
```

### Search for Entities

```python
from bccr_exchange_rates import search_entities, get_entity_by_name

# Search for all banks
banks = search_entities("Banco")
print(f"Found {len(banks)} banks")

# Search for financial companies
financieras = search_entities("Financiera")

# Get a specific entity by name
ari = get_entity_by_name("ARI")
if ari:
    print(f"ARI Exchange Rates:")
    print(f"  Buy:  ₡{ari['buy_rate']}")
    print(f"  Sell: ₡{ari['sell_rate']}")
    print(f"  Spread: ₡{ari['spread']}")

# Search with historical date
multimoney_oct = search_entities("MultiMoney", date="2025-10-15")
```

### Entity Data Structure

Each entity dictionary contains:

```python
{
    'entity_type': 'Financieras',           # Category name
    'entity_name': 'MultiMoney',            # Official entity name
    'buy_rate': 502.50,                     # Buy rate (Compra) in colones
    'sell_rate': 515.30,                    # Sell rate (Venta) in colones
    'spread': 12.80,                        # Differential (Diferencial Cambiario)
    'last_update': '2025-11-05T10:00:00',   # Last update timestamp (ISO format)
    'last_update_str': '05/11/2025 10:00 a.m.'  # Original timestamp string
}
```

### Advanced Usage

```python
from bccr_exchange_rates import scrape_ventanilla_page, group_entities_by_type

# Direct access to scraper for full metadata
result = scrape_ventanilla_page()
print(f"Date: {result['date']}")
print(f"Entities: {len(result['entities'])}")
print(f"Metadata: {result['metadata']}")

# Group entities manually
entities = result['entities']
grouped = group_entities_by_type(entities)
for entity_type, type_entities in grouped.items():
    avg_buy = sum(e['buy_rate'] for e in type_entities if e['buy_rate']) / len([e for e in type_entities if e['buy_rate']])
    print(f"{entity_type}: Average buy rate = ₡{avg_buy:.2f}")
```

## Entity Coverage

The library covers **7 entity categories** with **39+ total entities**:

| Category | Count | Examples |
|----------|-------|----------|
| **Bancos públicos** (Public banks) | 4 | Banco de Costa Rica, Banco Nacional |
| **Bancos privados** (Private banks) | 13 | BAC San José, Scotiabank, Cathay |
| **Financieras** (Finance companies) | 8 | MultiMoney, Desyfin, Acorde |
| **Casas de cambio** (Exchange houses) | 6 | ARI, Global Exchange, Inter Cambios |
| **Cooperativas** (Cooperatives) | 12 | Coopealianza, Coopeservidores |
| **Mutuales** (Mutual funds) | 2 | Mutual Cartago, Mutual Alajuela |
| **Puestos de Bolsa** (Stock brokers) | 11 | BCR Valores, Improsa |

## Error Handling

The library provides specific exceptions for different error scenarios:

```python
from bccr_exchange_rates import (
    get_current_rates,
    BCCRError,
    BCCRScrapingError,
    BCCRConnectionError,
    BCCRDateError
)

try:
    rates = get_current_rates()
except BCCRConnectionError as e:
    print(f"Connection failed: {e}")
except BCCRScrapingError as e:
    print(f"Scraping error: {e}")
except BCCRDateError as e:
    print(f"Date validation error: {e}")
except BCCRError as e:
    print(f"General BCCR error: {e}")
```

## Requirements

- Python 3.11 or higher
- requests >= 2.31.0
- beautifulsoup4 >= 4.12.0
- python-dateutil >= 2.8.0

## How It Works

This library scrapes the official BCCR ventanilla page:
https://gee.bccr.fi.cr/indicadoreseconomicos/Cuadros/frmConsultaTCVentanilla.aspx

**Scraping Method:**
- **Current data**: Direct HTTP GET request + BeautifulSoup parsing
- **Historical data**: Multi-step ASP.NET WebForms interaction with calendar controls

The library handles the complex ASP.NET ViewState management and calendar navigation automatically.

## Use Cases

- **Financial Applications**: Integrate live exchange rates into fintech apps
- **Price Comparison**: Build tools to find the best exchange rates
- **Currency Converters**: Create conversion tools with real market data
- **Data Analysis**: Analyze historical exchange rate trends
- **Automated Monitoring**: Track rate changes and send alerts
- **Business Intelligence**: Visualize currency market movements

## Limitations

- **No Real-time Updates**: Data is scraped on-demand, not pushed
- **Rate Limits**: Be respectful with requests to avoid overloading BCCR servers
- **Historical Data**: Requires Selenium for dates requiring calendar navigation

## Development

```bash
# Clone the repository
git clone https://github.com/jloria13/bccr-exchange-rates.git
cd bccr-exchange-rates

# Install in development mode
pip install -e ".[dev]"

```

## Contributing

Contributions are welcome! Please feel free to:
- Report bugs or issues
- Suggest new features
- Submit pull requests
- Improve documentation

## Acknowledgments

This library was inspired by [bccr-indicadores-economicos](https://github.com/andresmg07/bccr-indicadores-economicos) by Andrés Monge, which provided valuable insights into working with BCCR's economic indicators system.

## Related Projects

- **[bccr-exchange-api](https://github.com/jloria13/bccr-exchange-api)**: FastAPI wrapper providing REST API endpoints for this library

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Mauricio Loría

## Disclaimer

This is an unofficial library and is not affiliated with or endorsed by Banco Central de Costa Rica (BCCR).

**Important**:
- Use this library at your own discretion
- Always verify critical financial data with official sources
- Be respectful with request frequency to avoid overloading BCCR servers
- Exchange rates are for informational purposes only

## Support

- 📖 **Documentation**: This README and inline code documentation
- 🐛 **Issues**: [GitHub Issues](https://github.com/jloria13/bccr-exchange-rates/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/jloria13/bccr-exchange-rates/discussions)

---

Made with ❤️ in Costa Rica 🇨🇷
