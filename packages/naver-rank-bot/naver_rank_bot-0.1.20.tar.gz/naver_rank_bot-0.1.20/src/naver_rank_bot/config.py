#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
네이버 봇 설정 모듈

브라우저 설정, DOM 셀렉터, URL 상수를 정의합니다.
"""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class BrowserConfig:
    """
    NoDriver 브라우저 설정

    Attributes:
        DEFAULT_WINDOW_SIZE: 브라우저 창 크기 (1920x1080, 일반적인 해상도)
        PRODUCT_LOAD_TIMEOUT: 상품 로딩 대기 시간 (초)
        CAPTCHA_WAIT_TIME: 캡차 해결 대기 시간 (초, 수동 입력 허용)
        MAX_PAGINATION_ATTEMPTS: 최대 페이지네이션 시도 횟수
        BROWSER_ARGS: Chrome 실행 인자 (브라우저 자동화용)
            - AutomationControlled: 자동화 플래그 제어
            - IsolateOrigins: 사이트 격리 비활성화 (성능 개선)
            - no-sandbox: 샌드박스 비활성화 (root 실행 시 필수)
            - disable-dev-shm-usage: 공유 메모리 사용 안 함 (Docker 호환)
            - disable-gpu: GPU 가속 비활성화 (안정성 향상)
            - start-maximized: 최대화 시작

    Note:
        이 설정들은 NoDriver 브라우저 자동화를 위한 표준 구성입니다.
        설정 변경 시 브라우저 동작이 불안정해질 수 있습니다.
    """
    DEFAULT_WINDOW_SIZE: str = '1920,1080'
    PRODUCT_LOAD_TIMEOUT: int = 30
    CAPTCHA_WAIT_TIME: int = 120
    MAX_PAGINATION_ATTEMPTS: int = 30

    # 브라우저 인자
    BROWSER_ARGS: Tuple[str, ...] = (
        # 브라우저 자동화 설정
        '--disable-blink-features=AutomationControlled',
        '--disable-features=IsolateOrigins,site-per-process',
        '--disable-site-isolation-trials',
        # 필수 플래그 (서버 환경)
        '--no-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
        '--start-maximized',
        # 안정성 향상 플래그 (Lightsail 등 클라우드 환경)
        '--disable-software-rasterizer',
        '--disable-extensions',
        '--disable-background-networking',
        '--disable-sync',
        '--disable-default-apps',
        '--mute-audio',
        '--no-first-run',
        '--disable-setuid-sandbox',
        '--disable-background-timer-throttling',
        '--disable-renderer-backgrounding',
        '--disable-backgrounding-occluded-windows',
        '--disable-hang-monitor',
        '--disable-prompt-on-repost',
        '--disable-domain-reliability'
    )


@dataclass(frozen=True)
class Selectors:
    """
    네이버 쇼핑 DOM 셀렉터 모음

    네이버가 DOM 구조를 변경할 때를 대비해 여러 대체 셀렉터를 제공합니다.
    봇이 상품을 찾지 못하는 경우 이 클래스를 먼저 확인하세요.

    Attributes:
        MAIN_SEARCH_BOX: 네이버 메인 페이지 검색창 (우선순위 순)
        MAIN_SEARCH_BUTTON: 네이버 메인 검색 버튼
        PRICE_COMPARE_BUTTON: 쇼핑 페이지로 이동하는 "가격비교 더보기" 버튼
        PRODUCT_ITEMS: 모든 상품 타입 (광고, 슈퍼적립, 일반 포함)
        AD_PRODUCTS: 광고 상품만 (adProduct_item__ 클래스)
        REGULAR_PRODUCTS: 일반 상품만 (product_item__ 클래스)
        SUPER_SAVING_PRODUCTS: 슈퍼적립 상품 (광고로 분류)
        NEXT_PAGE_BUTTON: 다음 페이지 버튼

    Note:
        네이버는 빌드마다 클래스명에 해시를 추가합니다 (예: product_item__xyz123).
        와일드카드 셀렉터 ([class*='product_item__'])를 사용하여 해시 변경에 대응합니다.

    Warning:
        이 셀렉터들이 작동하지 않으면 네이버가 DOM을 변경한 것입니다.
        page_1_after_scroll.html을 확인하여 새로운 셀렉터를 찾으세요.
    """
    # 네이버 메인 검색창
    MAIN_SEARCH_BOX: Tuple[str, ...] = (
        "input#query",
        "input[name='query'][type='search']",
        "input.search_input",
        "input[placeholder='검색어를 입력해 주세요.']"
    )

    # 네이버 메인 검색 버튼
    MAIN_SEARCH_BUTTON: Tuple[str, ...] = (
        "button.btn_search",
        "button[type='submit'].btn_search",
        "button:has(svg#search-btn)",
        "button[onclick*='nclick']"
    )

    # 가격비교 더보기 버튼
    PRICE_COMPARE_BUTTON: Tuple[str, ...] = (
        "a[href*='search.shopping.naver.com']",
        "a.OCNh8KJm",
        "a[target='_blank'][href*='shopping']"
    )

    # 상품 요소
    PRODUCT_ITEMS: str = "div[class*='product_item__'], div[class*='adProduct_item__'], div[class*='superSavingProduct_item__']"
    AD_PRODUCTS: str = "div[class*='adProduct_item__']"
    REGULAR_PRODUCTS: str = "div[class*='product_item__']"
    SUPER_SAVING_PRODUCTS: str = "div[class*='superSavingProduct_item__']"

    # 페이지네이션
    NEXT_PAGE_BUTTON: str = "a.pagination_next__kh_cw"


@dataclass(frozen=True)
class URLs:
    """
    네이버 URL 상수

    Attributes:
        NAVER_HOME: 네이버 메인 페이지 (검색 시작점)
        SHOPPING_SEARCH: 쇼핑 검색 페이지 템플릿 ({} 부분에 키워드 삽입)
    """
    NAVER_HOME: str = "https://www.naver.com"
    SHOPPING_SEARCH: str = "https://search.shopping.naver.com/search/all?query={}"
