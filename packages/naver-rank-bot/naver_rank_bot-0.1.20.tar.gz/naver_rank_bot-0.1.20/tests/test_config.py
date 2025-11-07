"""
Tests for config module
"""
import pytest
from naver_rank_bot import BrowserConfig, Selectors, URLs


def test_browser_config():
    """Test BrowserConfig constants"""
    assert BrowserConfig.DEFAULT_WINDOW_SIZE == '1920,1080'
    assert BrowserConfig.PRODUCT_LOAD_TIMEOUT == 30
    assert BrowserConfig.CAPTCHA_WAIT_TIME == 120
    assert BrowserConfig.MAX_PAGINATION_ATTEMPTS == 30

    # Test critical browser args
    assert '--disable-blink-features=AutomationControlled' in BrowserConfig.BROWSER_ARGS
    assert '--no-sandbox' in BrowserConfig.BROWSER_ARGS


def test_selectors():
    """Test Selectors constants"""
    assert len(Selectors.MAIN_SEARCH_BOX) > 0
    assert len(Selectors.MAIN_SEARCH_BUTTON) > 0
    assert 'product_item__' in Selectors.PRODUCT_ITEMS
    assert 'adProduct_item__' in Selectors.AD_PRODUCTS


def test_urls():
    """Test URLs constants"""
    assert URLs.NAVER_HOME == "https://www.naver.com"
    assert 'search.shopping.naver.com' in URLs.SHOPPING_SEARCH
    assert '{}' in URLs.SHOPPING_SEARCH
