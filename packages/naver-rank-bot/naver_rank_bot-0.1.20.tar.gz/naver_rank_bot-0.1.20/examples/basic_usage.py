#!/usr/bin/env python3
"""
Basic usage example for Naver Rank Bot
"""

import asyncio
import json
from pathlib import Path
from naver_rank_bot import NaverRankBot


def load_config():
    """Load configuration from config.json or use defaults"""
    config_path = Path(__file__).parent / "config.json"

    # Default configuration
    default_config = {
        "products": [{
            "keyword": "아식스 테니스화",
            "product_no": "12345678",
            "name": "Example Product"
        }],
        "bot_settings": {
            "headless": False,
            "max_pages": 10
        }
    }

    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print(f"⚠️  Config file not found at {config_path}")
        print("📝 Using default configuration. Create config.json from config.example.json to customize.")
        return default_config


async def main():
    """
    Basic example: Search for a product and get its ranking
    """
    # Load configuration
    config = load_config()
    bot_settings = config.get("bot_settings", {})
    products = config.get("products", [])

    if not products:
        print("❌ No products configured. Please add products to config.json")
        return

    # Use first product for basic example
    product = products[0]

    # Create bot instance
    bot = NaverRankBot(
        headless=bot_settings.get("headless", False),
        log_file=bot_settings.get("log_file"),  # None이면 콘솔만 출력
        user_data_dir=bot_settings.get("user_data_dir"),
        debug=bot_settings.get("debug", False)  # True면 .debug/에 디버그 파일 저장
    )

    try:
        # Search for product ranking
        result = await bot.search_product_rank(
            keyword=product["keyword"],
            target_product_no=product.get("product_no"),
            max_pages=bot_settings.get("max_pages", 10)
        )

        # Display results
        print("\n" + "="*50)
        print("Search Results")
        print("="*50)

        if result['found']:
            print(f"✅ Product Found!")
            print(f"   Rank (with ads): {result.get('rank_with_ads')}")
            print(f"   Rank (without ads): {result.get('rank_without_ads')}")

            if result.get('ad_found'):
                print(f"\n📢 Ad Placement:")
                print(f"   Ad Rank: {result.get('ad_rank')}")
                print(f"   Ad Page: {result.get('ad_page')}")
        else:
            print(f"❌ Product not found")
            if 'message' in result:
                print(f"   Message: {result['message']}")

    finally:
        # Always close the bot to cleanup resources
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
