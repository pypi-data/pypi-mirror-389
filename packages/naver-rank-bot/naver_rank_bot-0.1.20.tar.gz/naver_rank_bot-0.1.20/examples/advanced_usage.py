#!/usr/bin/env python3
"""
Advanced usage example with profile reuse and multiple searches
"""

import asyncio
import json
from pathlib import Path
from naver_rank_bot import NaverRankBot

def load_config():
    """Load configuration from config.json"""
    config_path = Path(__file__).parent / "config.json"

    # Default configuration
    default_config = {
        "products": [
            {
                "keyword": "아식스 테니스화",
                "product_no": "12345678",
                "name": "ASICS Court FF 3"
            },
            {
                "keyword": "나이키 러닝화",
                "product_no": "87654321",
                "name": "Nike Pegasus 40"
            }
        ],
        "bot_settings": {
            "headless": False,
            "user_data_dir": "nodriver_profiles/my_profile",
            "max_pages": 20,
            "delay_between_searches": 10
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
    Advanced example: Multiple searches with profile reuse
    """
    # Load configuration
    config = load_config()
    bot_settings = config.get("bot_settings", {})
    products = config.get("products", [])

    if not products:
        print("❌ No products configured. Please add products to config.json")
        return

    # Create bot instance with profile
    bot = NaverRankBot(
        headless=bot_settings.get("headless", False),
        log_file=bot_settings.get("log_file"),  # None이면 콘솔만 출력
        user_data_dir=bot_settings.get("user_data_dir"),
        debug=bot_settings.get("debug", False)  # True면 .debug/에 디버그 파일 저장
    )

    try:
        results = []

        for product in products:
            print(f"\n검색 중: {product['name']}...")

            result = await bot.search_product_rank(
                keyword=product['keyword'],
                target_product_no=product.get('product_no'),
                max_pages=bot_settings.get("max_pages", 20)
            )

            results.append({
                **product,
                **result
            })

            # Wait between searches for service stability
            delay = bot_settings.get("delay_between_searches", 10)
            if len(products) > 1:  # Only delay if there are multiple products
                await asyncio.sleep(delay)

        # Print summary
        print("\n" + "="*70)
        print("Ranking Summary")
        print("="*70)

        for r in results:
            print(f"\n{r['name']}:")
            if r['found']:
                print(f"  ✅ Rank: {r.get('rank_without_ads', 'N/A')}")
                if r.get('ad_found'):
                    print(f"  📢 Ad Rank: {r.get('ad_rank', 'N/A')}")
            else:
                print(f"  ❌ Not found in top {r.get('max_pages', 20)} pages")

    finally:
        await bot.close()


if __name__ == "__main__":
    asyncio.run(main())
