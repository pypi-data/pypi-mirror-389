# Naver Rank Bot

Browser automation tool for analyzing Naver SmartStore product rankings. Built with NoDriver for reliable automated browsing.

## Features

- **Browser Automation**: Uses NoDriver for automated browser control and interaction
- **Reliable Operation**: Optimized browser configuration for stable automated browsing
- **Product Ranking Analysis**: Analyze product rankings in Naver SmartStore search results
- **Ad Detection**: Separate tracking for ad placements and organic rankings
- **Natural Interaction**: Implements delays and natural interaction patterns
- **Pagination Support**: Automatic multi-page search with configurable limits

## Installation

### Prerequisites

Install [uv](https://github.com/astral-sh/uv) - a fast Python package manager:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### From Source (Recommended)

```bash
git clone https://github.com/marqetly/naver-rank-bot.git
cd naver-rank-bot
uv sync  # Creates venv and installs dependencies
```

### Using UV

```bash
uv pip install naver-rank-bot
```

### Using pip (Alternative)

```bash
pip install naver-rank-bot
```

## Quick Start

### Using Examples (Recommended)

The easiest way to get started is using the provided examples with configuration:

```bash
# Navigate to examples directory
cd examples

# Create config from template
cp config.example.json config.json

# Edit config.json with your product information
# Then run:
python basic_usage.py
```

### Manual Usage

You can also use the bot directly in Python:

```python
import asyncio
from naver_rank_bot import NaverRankBot

async def main():
    bot = NaverRankBot(headless=False)

    result = await bot.search_product_rank(
        keyword="아식스 테니스화",
        target_product_no="12345678",
        max_pages=10
    )

    print(f"Found: {result['found']}")
    print(f"Rank (with ads): {result.get('rank_with_ads')}")
    print(f"Rank (without ads): {result.get('rank_without_ads')}")

    await bot.close()

if __name__ == "__main__":
    asyncio.run(main())
```

Run with: `uv run python your_script.py`

## Configuration

### Browser Configuration

```python
from naver_rank_bot import BrowserConfig

# Access configuration constants
window_size = BrowserConfig.DEFAULT_WINDOW_SIZE
timeout = BrowserConfig.PRODUCT_LOAD_TIMEOUT
```

### Selectors

DOM selectors are defined in `Selectors` class. If Naver changes their structure, update these:

```python
from naver_rank_bot import Selectors

# Check current selectors
print(Selectors.PRODUCT_ITEMS)
print(Selectors.AD_PRODUCTS)
```

## API Reference

### `NaverRankBot`

Main bot class for Naver product ranking searches.

#### Methods

##### `__init__(headless: bool = False, log_file: Optional[str] = None, user_data_dir: Optional[str] = None, debug: bool = False)`

Create a new bot instance.

**Parameters:**
- `headless` (bool): Run browser in headless mode. Default: False (visible mode recommended for reliability)
- `log_file` (Optional[str]): Log file path. Default: None (console only). Example: 'logs/naver_bot.log'
- `user_data_dir` (Optional[str]): Path to Chrome user data directory for profile reuse
- `debug` (bool): Enable debug mode. Default: False. When True, saves screenshots and HTML to `.debug/` folder

##### `async search_product_rank(...)`

Search for product ranking in Naver SmartStore.

**Parameters:**
- `keyword` (str): Search keyword
- `target_product_no` (Optional[str]): Product number to match (recommended)
- `target_product` (Optional[str]): Product name to match (fallback)
- `target_store` (Optional[str]): Store name for additional matching
- `max_pages` (int): Maximum pages to search. Default: 30

**Returns:**
```python
{
    'found': bool,              # Product found
    'ad_found': bool,          # Ad version found
    'rank_with_ads': int,      # Rank including ads
    'rank_without_ads': int,   # Rank excluding ads
    'ad_rank': int,            # Ad placement rank
    'ad_page': int,            # Page where ad found
    'message': str             # Error or info message
}
```

##### `async close()`

Close the browser and cleanup resources.

## Architecture

```
naver_rank_bot/
├── __init__.py          # Package exports
├── config.py            # BrowserConfig, Selectors, URLs
├── js_evaluator.py      # JavaScript evaluation utilities
└── bot.py               # NaverRankBot main class
```

### Modules

- **config.py**: Configuration constants and DOM selectors
- **js_evaluator.py**: JavaScript templates for DOM evaluation
- **bot.py**: Main bot implementation with search logic

## Technical Implementation

This tool uses several techniques for reliable browser automation:

1. **NoDriver**: Advanced ChromeDriver alternative for browser automation
2. **Browser Configuration**: Optimized flags for stable operation
3. **Natural Interaction**: Implements delays and natural interaction patterns
4. **Profile Reuse**: Supports Chrome profile reuse for consistent behavior
5. **Visible Mode**: Headless mode is optional (visible mode recommended)

### Browser Configuration

```python
'--disable-blink-features=AutomationControlled'  # Standard automation flag
'--disable-features=IsolateOrigins,site-per-process'
'--window-size=1920,1080'  # Standard browser dimensions
```

## Troubleshooting

### Bot Not Finding Products

1. Check if Naver changed DOM structure
2. Inspect `page_1_after_scroll.html` (saved during search)
3. Update selectors in `Selectors` class

### Frequent Captchas

- Reduce search frequency (wait 10+ minutes between searches)
- Use real Chrome profile (`user_data_dir`)
- Never use `headless=True` in production

### Browser Won't Start

```bash
# Clear browser profiles
rm -rf nodriver_profiles/*

# Verify Chrome installation
which google-chrome || which chromium
```

## Usage Recommendations

For responsible and reliable operation:

- Limit to 10-20 searches per day per profile
- Wait 5-10 minutes between searches to avoid rate limiting
- Never run multiple instances with same profile
- Visible mode (headless=False) is more reliable than headless mode

## Requirements

- Python 3.11+
- NoDriver 0.35.0+
- Chrome or Chromium browser

## License

AGPL-3.0-or-later License

This project uses [NoDriver](https://github.com/ultrafunkamsterdam/nodriver) which is licensed under AGPL-3.0. Therefore, this project must also be licensed under AGPL-3.0 or later.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Disclaimer

**IMPORTANT LEGAL NOTICE:**

This software is provided for educational and research purposes only. By using this software, you acknowledge and agree to the following:

1. **Terms of Service Compliance**: You are solely responsible for ensuring your use complies with Naver's Terms of Service and all applicable laws and regulations in your jurisdiction.

2. **Prohibited Activities**: This software should NOT be used for:
   - Violating any website's Terms of Service or robots.txt
   - Circumventing access controls or security measures
   - Any commercial use without proper authorization
   - Any activity that may be considered illegal or unauthorized

3. **No Warranty**: This software is provided "AS IS" without any warranties. The authors make no representations about the legality of using this software in any particular jurisdiction.

4. **Limitation of Liability**: The authors and contributors are not responsible for any misuse, legal consequences, or damages arising from the use of this software.

5. **User Responsibility**: Users must obtain proper authorization before automating access to any website or service. You are solely responsible for your actions and their consequences.

**By using this software, you agree to use it responsibly and at your own risk.**
