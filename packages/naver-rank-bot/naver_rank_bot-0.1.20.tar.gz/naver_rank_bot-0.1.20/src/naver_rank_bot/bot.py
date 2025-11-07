#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
NoDriver 기반 네이버 스마트스토어 상품 순위 검색 봇

메인 봇 클래스와 검색 로직을 포함합니다.
"""

import asyncio
import logging
import random
import urllib.parse
from typing import Optional, Dict, List, Any, Tuple

import nodriver as uc

from .config import BrowserConfig, Selectors, URLs
from .js_evaluator import JSEvaluator, unwrap_nodriver_response


class NaverRankBot:
    """
    NoDriver 기반 네이버 스마트스토어 상품 순위 검색 봇

    NoDriver를 사용한 브라우저 자동화를 통해 네이버 쇼핑 검색 결과에서
    상품 순위를 분석합니다.

    주요 기능:
        - 네이버 쇼핑 검색 및 상품 순위 추적
        - 광고 상품과 일반 상품 구분
        - 자동 페이지네이션 (최대 30페이지)
        - 자연스러운 상호작용 패턴 (랜덤 지연, 점진적 타이핑)

    검색 흐름:
        1. naver.com 접속
        2. 검색어 입력
        3. 쇼핑 페이지로 이동
        4. 페이지네이션하며 상품 추출
        5. 대상 상품 매칭 (상품번호 또는 상품명)
        6. 광고/일반 순위 반환

    Attributes:
        headless: 헤드리스 모드 여부 (False 권장)
        log_file: 로그 파일 경로 (None이면 콘솔만 출력)
        user_data_dir: Chrome 프로필 디렉토리 (재사용 권장)
        profile_name: Chrome 프로필 이름
        debug: 디버그 모드 (True이면 .debug/ 폴더에 스크린샷/HTML 저장)
        driver: NoDriver 브라우저 인스턴스
        logger: 로거 인스턴스
        config: 브라우저 설정
        selectors: DOM 셀렉터
        urls: URL 상수
        js: JavaScript 평가기

    Example:
        >>> # 기본 사용 (콘솔 로그만, 디버그 파일 없음)
        >>> bot = NaverRankBot(headless=False, user_data_dir='./profiles/naver')
        >>>
        >>> # 로그 파일 사용
        >>> bot = NaverRankBot(
        ...     headless=False,
        ...     log_file='logs/naver_bot.log',
        ...     user_data_dir='./profiles/naver'
        ... )
        >>>
        >>> # 디버그 모드 (스크린샷 및 HTML 저장)
        >>> bot = NaverRankBot(
        ...     headless=False,
        ...     log_file='logs/naver_bot.log',
        ...     user_data_dir='./profiles/naver',
        ...     debug=True
        ... )
        >>>
        >>> result = await bot.search_product_rank(
        ...     keyword="드럼바",
        ...     target_product_no="82467473814",
        ...     max_pages=10
        ... )
        >>> print(f"Found at rank: {result['rank_with_ads']}")
        >>> await bot.close()

    Note:
        - 하루 10-20회 검색 제한 권장 (서비스 안정성 고려)
        - 검색 간 5-10분 대기 권장
        - headless=False (가시 모드) 권장
        - user_data_dir 재사용으로 브라우징 히스토리 유지
    """

    def __init__(
        self,
        headless: bool = False,
        log_file: Optional[str] = None,
        user_data_dir: Optional[str] = None,
        profile_name: str = 'Default',
        debug: bool = False
    ):
        """
        NaverRankBot 초기화

        Args:
            headless: 헤드리스 모드 활성화 여부 (기본값: False)
                False 권장 - 가시 모드가 더 안정적
            log_file: 로그 파일 경로 (기본값: None, 콘솔만 출력)
                지정하면 해당 경로에 로그 파일 생성
                예: 'logs/naver_bot.log', 'naver_rank.log'
            user_data_dir: Chrome 사용자 데이터 디렉토리 (기본값: None)
                지정하면 브라우징 히스토리가 유지되어 안정성 향상
            profile_name: Chrome 프로필 이름 (기본값: 'Default')
            debug: 디버그 모드 활성화 (기본값: False)
                True로 설정하면 .debug/ 폴더에 스크린샷과 HTML 저장

        Note:
            - user_data_dir을 지정하지 않으면 매번 새로운 프로필이 생성됩니다.
            - 재사용을 위해 './profiles/naver' 같은 경로 지정을 권장합니다.
            - log_file을 None으로 두면 콘솔에만 로그가 출력됩니다.
            - debug=True로 설정하면 .debug/ 폴더가 자동 생성되고 디버그 파일이 저장됩니다.
        """
        self.headless = headless
        self.log_file = log_file or None
        self.user_data_dir = user_data_dir
        self.profile_name = profile_name
        self.debug = debug
        self.driver: Optional[uc.Browser] = None
        self.logger = self._setup_logging()
        self.config = BrowserConfig()
        self.selectors = Selectors()
        self.urls = URLs()
        self.js = JSEvaluator()

    def _setup_logging(self) -> logging.Logger:
        """로깅 설정"""
        handlers = [logging.StreamHandler()]

        # 로그 파일이 지정된 경우에만 파일 핸들러 추가
        if self.log_file:
            from pathlib import Path
            log_path = Path(self.log_file)

            # 로그 디렉토리가 없으면 생성
            if log_path.parent != Path('.'):
                log_path.parent.mkdir(parents=True, exist_ok=True)

            handlers.append(logging.FileHandler(self.log_file, encoding='utf-8'))

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=handlers,
            force=True  # 기존 설정 덮어쓰기
        )

        # NoDriver의 asyncio 태스크 에러 로깅 억제
        # (브라우저 종료 시 발생하는 무해한 백그라운드 태스크 에러)
        asyncio_logger = logging.getLogger('asyncio')
        asyncio_logger.setLevel(logging.CRITICAL)

        return logging.getLogger(__name__)

    async def random_wait(self, min_sec: float = 1, max_sec: float = 3) -> None:
        """비동기 랜덤 대기"""
        wait_time = random.uniform(min_sec, max_sec)
        await asyncio.sleep(wait_time)

    async def human_like_typing(self, element: Any, text: str) -> None:
        """인간처럼 타이핑 (자연스러운 지연)"""
        for char in text:
            await element.send_keys(char)
            await asyncio.sleep(random.uniform(0.1, 0.3))

    async def _start_browser(self) -> uc.Browser:
        """브라우저 시작 및 설정"""
        self.logger.info("NoDriver 브라우저 시작...")

        config = uc.Config()
        config.headless = self.headless
        if self.user_data_dir:
            config.user_data_dir = self.user_data_dir

        browser_args = [
            f'--window-size={self.config.DEFAULT_WINDOW_SIZE}',
            *self.config.BROWSER_ARGS
        ]

        try:
            return await uc.start(config=config, browser_args=browser_args)
        except Exception as e:
            # 브라우저 연결 실패 시 더 자세한 에러 메시지
            self.logger.error(f"브라우저 시작 실패: {e}")
            self.logger.error("\n해결 방법:")
            self.logger.error("1. Chrome 설치: brew install --cask google-chrome")
            self.logger.error("2. 또는 Chromium 설치: brew install --cask chromium")
            self.logger.error("3. 권한 확인: Chrome이 시스템 보안 설정에서 허용되었는지 확인")
            self.logger.error("4. 프로필 디렉토리 삭제 후 재시도: rm -rf nodriver_profiles")
            raise

    async def _find_element_by_selectors(
        self,
        page: Any,
        selectors: Tuple[str, ...],
        element_name: str
    ) -> Optional[Any]:
        """여러 셀렉터를 순회하며 요소 찾기"""
        for selector in selectors:
            try:
                elements = await page.find_all(selector)
                if elements and len(elements) > 0:
                    self.logger.info(f"{element_name} 찾음: {selector}")
                    return elements[0]
            except Exception:
                continue
        return None

    async def _navigate_to_naver_home(self, page: Any) -> None:
        """네이버 홈페이지로 이동 및 자연스러운 동작 수행"""
        await page
        # await self.random_wait(3, 5)

        # 자연스러운 스크롤
        # await page.scroll_down(200 + random.randint(0, 200))
        # await self.random_wait(1, 2)

    async def _perform_main_search(self, page: Any, keyword: str) -> None:
        """네이버 메인 검색창에서 키워드 검색"""
        self.logger.info("STEP 1: 네이버 메인 검색창에서 키워드 입력...")

        # 검색창 찾기
        search_box = await self._find_element_by_selectors(
            page,
            self.selectors.MAIN_SEARCH_BOX,
            "네이버 메인 검색창"
        )

        if not search_box:
            raise Exception("네이버 메인 검색창을 찾을 수 없습니다")

        # 검색창 마우스 호버 및 클릭
        await search_box.mouse_move()
        await self.random_wait(0.3, 0.7)
        await search_box.click()
        await self.random_wait(0.5, 1)

        # 기존 텍스트 지우기
        try:
            if hasattr(search_box, 'clear'):
                result = search_box.clear()
                if asyncio.iscoroutine(result):
                    await result
        except Exception:
            pass

        await self.random_wait(0.5, 1)

        # 인간처럼 타이핑
        self.logger.info(f"검색어 입력: {keyword}")
        await self.human_like_typing(search_box, keyword)
        await self.random_wait(1, 2)

        # 검색 버튼 클릭
        await self._click_main_search_button(page, search_box)

    async def _click_main_search_button(self, page: Any, search_box: Any) -> None:
        """네이버 메인 검색 버튼 클릭"""
        self.logger.info("STEP 2: 네이버 메인 검색 버튼 클릭...")

        search_button = await self._find_element_by_selectors(
            page,
            self.selectors.MAIN_SEARCH_BUTTON,
            "네이버 메인 검색 버튼"
        )

        if search_button:
            self.logger.info("네이버 메인 검색 버튼 마우스 호버 후 클릭")
            await search_button.mouse_move()
            await self.random_wait(0.3, 0.7)
            await search_button.click()
        else:
            self.logger.info("검색 버튼을 찾지 못해 Enter 키 입력")
            await search_box.send_keys("\n")

        await self.random_wait(3, 5)

    async def _navigate_to_shopping_page(self, page: Any, keyword: str) -> Any:
        """쇼핑 검색 페이지로 이동"""
        self.logger.info("STEP 3: '가격비교 더보기' 버튼 찾기 및 클릭...")

        await self.random_wait(2, 3)

        # '가격비교 더보기' 버튼 찾기
        price_compare_button = None
        for _ in range(3):
            price_compare_button = await self._find_price_compare_button(page)
            if price_compare_button:
                break
            await self.random_wait(1, 2)

        if price_compare_button:
            self.logger.info("'가격비교 더보기' 버튼 마우스 호버 후 클릭")
            await price_compare_button.mouse_move()
            await self.random_wait(0.5, 1.0)
            await price_compare_button.click()
            await self.random_wait(3, 5)

            # 새 탭 전환
            page = await self._switch_to_shopping_tab()
        else:
            # 직접 URL로 이동
            page = await self._navigate_direct_to_shopping(keyword)

        return page

    async def _find_price_compare_button(self, page: Any) -> Optional[Any]:
        """가격비교 더보기 버튼 찾기"""
        for selector in self.selectors.PRICE_COMPARE_BUTTON:
            try:
                elements = await page.find_all(selector)
                for elem in elements:
                    try:
                        href = await elem.get_attribute('href') if hasattr(elem, 'get_attribute') else None
                        if href and 'search.shopping.naver.com' in href:
                            self.logger.info(f"'가격비교 더보기' 버튼 찾음 (href: {href[:50]}...)")
                            return elem
                    except Exception:
                        continue
            except Exception:
                continue

        # 텍스트로 찾기
        try:
            button = await page.find("네이버 가격비교 더보기", best_match=True)
            if button:
                self.logger.info("텍스트로 '가격비교 더보기' 버튼 찾음")
                return button
        except Exception:
            pass

        return None

    async def _switch_to_shopping_tab(self) -> Any:
        """새로 열린 쇼핑 탭으로 전환"""
        try:
            tabs = self.driver.tabs if hasattr(self.driver, 'tabs') else []
            if not tabs:
                tabs = await self.driver.get_tabs() if hasattr(self.driver, 'get_tabs') else []

            if tabs and len(tabs) > 1:
                page = tabs[-1]
                if hasattr(page, 'bring_to_front'):
                    await page.bring_to_front()
                self.logger.info("쇼핑 검색 결과 페이지로 전환 완료")
                return page
        except Exception:
            pass

        return self.driver.tabs[0] if self.driver.tabs else None

    async def _navigate_direct_to_shopping(self, keyword: str) -> Any:
        """직접 쇼핑 검색 URL로 이동"""
        self.logger.info("'가격비교 더보기' 버튼을 찾지 못해 직접 쇼핑 검색 URL로 이동")
        encoded_keyword = urllib.parse.quote(keyword)
        search_url = self.urls.SHOPPING_SEARCH.format(encoded_keyword)
        page = await self.driver.get(search_url)
        await self.random_wait(3, 5)
        return page

    async def _wait_for_products_to_load(self, page: Any) -> bool:
        """상품 로딩 대기"""
        self.logger.info("상품 로딩 대기 중...")

        for _ in range(self.config.PRODUCT_LOAD_TIMEOUT):
            product_count = await page.evaluate(self.js.get_product_count())
            if product_count > 0:
                self.logger.info(f"상품 로딩 완료 ({product_count}개 상품 감지)")
                return True
            await asyncio.sleep(1)

        self.logger.warning("상품 로딩 타임아웃")
        return False

    async def _check_for_captcha(self, page: Any) -> bool:
        """캡차 확인 및 대기"""
        page_content = await page.get_content()

        if any(keyword in page_content for keyword in ["자동입력 방지", "캡차", "영수증"]):
            self.logger.warning("🤖 캡차 감지! 수동으로 해결해주세요.")
            self.logger.info(f"{self.config.CAPTCHA_WAIT_TIME}초 대기 중...")
            await asyncio.sleep(self.config.CAPTCHA_WAIT_TIME)

            # 재확인
            page_content = await page.get_content()
            if "자동입력 방지" in page_content:
                self.logger.error("캡차가 해결되지 않았습니다.")
                return False

        return True

    async def _check_for_blocking(self, page: Any) -> bool:
        """차단 여부 확인"""
        page_content = await page.get_content()

        if "일시적으로 제한" in page_content:
            self.logger.error("네이버가 차단 중입니다.")

            if self.debug:
                from pathlib import Path
                debug_dir = Path('.debug')
                debug_dir.mkdir(exist_ok=True)
                screenshot_path = debug_dir / "blocked_nodriver.png"
                await page.save_screenshot(str(screenshot_path))
                self.logger.info(f"차단 스크린샷 저장: {screenshot_path}")

            return True

        return False

    async def _scroll_page_to_load_all_products(self, page: Any) -> None:
        """페이지를 스크롤하여 모든 상품 로드"""
        self.logger.info("페이지 스크롤하여 모든 상품 로드 중...")

        last_height = await page.evaluate(self.js.get_body_height())

        while True:
            await page.evaluate(self.js.scroll_to_bottom())
            await self.random_wait(2, 3)

            new_height = await page.evaluate(self.js.get_body_height())

            if new_height == last_height:
                break
            last_height = new_height

        self.logger.info("모든 상품 로드 완료")

    async def _extract_products_from_page(self, page: Any) -> List[Dict[str, Any]]:
        """페이지에서 상품 정보 추출"""
        try:
            self.logger.info("JavaScript로 상품 정보 추출 시도...")
            products_info = await page.evaluate(self.js.extract_all_products())

            # NoDriver 응답 형식 변환
            if isinstance(products_info, list):
                products_info = [unwrap_nodriver_response(p) for p in products_info]

            return products_info

        except Exception as e:
            self.logger.error(f"JavaScript evaluate 실패: {e}")
            self.logger.info("대체 방법: NoDriver의 find_all 사용")
            return await self._extract_products_fallback(page)

    async def _extract_products_fallback(self, page: Any) -> List[Dict[str, Any]]:
        """대체 방법으로 상품 정보 추출"""
        products_info = []

        try:
            # 광고 상품
            ad_products = await page.find_all(self.selectors.AD_PRODUCTS)
            for i, product in enumerate(ad_products or []):
                products_info.append({
                    'type': 'ad',
                    'is_ad': True,
                    'title': '',
                    'store': '',
                    'price': '',
                    'element': product,
                    'index': i
                })

            # 일반 상품
            regular_products = await page.find_all(self.selectors.REGULAR_PRODUCTS)
            for i, product in enumerate(regular_products or []):
                products_info.append({
                    'type': 'regular',
                    'is_ad': False,
                    'title': '',
                    'store': '',
                    'price': '',
                    'element': product,
                    'index': i
                })

        except Exception as e:
            self.logger.error(f"대체 방법도 실패: {e}")

        return products_info

    async def _navigate_to_next_page(self, page: Any) -> bool:
        """다음 페이지로 이동"""
        try:
            # 페이지 하단으로 스크롤
            await page.evaluate(self.js.scroll_to_bottom())
            await self.random_wait(1, 2)

            self.logger.info("  '다음' 버튼 찾는 중...")

            # 다음 버튼 찾기
            try:
                next_button = await page.find(self.selectors.NEXT_PAGE_BUTTON, timeout=5)
            except Exception as e:
                self.logger.warning(f"  '다음' 버튼 찾기 실패: {e}")
                self.logger.info("더 이상 페이지가 없습니다.")
                return False

            self.logger.info("  '다음' 버튼 찾음, 마우스 호버 후 클릭 시도...")

            # 자연스러운 마우스 이동 및 호버
            await next_button.mouse_move()
            await self.random_wait(0.5, 1.5)

            # 클릭
            await next_button.click()
            await self.random_wait(3, 5)

            # 상품 로딩 대기
            for _ in range(self.config.MAX_PAGINATION_ATTEMPTS):
                try:
                    product_count = await page.evaluate(self.js.get_product_count())
                    if product_count > 0:
                        self.logger.info(f"  상품 로딩 완료 ({product_count}개 상품 감지)")
                        return True
                except Exception:
                    pass
                await asyncio.sleep(1)

            return True

        except Exception as e:
            self.logger.warning(f"페이지 이동 실패: {e}")
            return False

    def _match_product(
        self,
        product_name: str,
        store_name: str,
        product_no: str,
        target_product: Optional[str],
        target_store: Optional[str],
        target_product_no: Optional[str]
    ) -> bool:
        """
        상품 매칭 여부 확인

        Args:
            product_name: 상품명
            store_name: 스토어명
            product_no: 상품번호 (nv_mid 또는 chnl_prod_no)
            target_product: 찾을 상품명 (옵션)
            target_store: 찾을 스토어명 (옵션)
            target_product_no: 찾을 상품번호 (옵션)

        Returns:
            매칭 여부 (True/False)
        """
        # 1순위: Product No로 매칭 (가장 정확)
        if target_product_no and product_no:
            if target_product_no == product_no:
                return True
            # 부분 매칭도 허용 (긴 번호의 경우)
            if target_product_no in product_no or product_no in target_product_no:
                return True

        # 2순위: 상품명으로 매칭
        if target_product:
            if not product_name:
                return False

            if target_product.lower() not in product_name.lower():
                return False

            # 스토어명 추가 검증 (옵션)
            if target_store and store_name:
                return target_store.lower() in store_name.lower()

            return True

        return False

    def _format_product_log(
        self,
        rank: int,
        product_type: str,
        product_name: str,
        store_name: str,
        price: str,
        product_no: str = ''
    ) -> None:
        """상품 로그 포맷팅 및 출력"""
        type_marks = {
            'ad': '[광고]',
            'super': '[슈퍼적립]',
            'regular': '[일반]'
        }
        type_mark = type_marks.get(product_type, '[알 수 없음]')

        log_msg = (
            f"  {rank}위 {type_mark} "
            f"{product_name if product_name else '상품명 없음'} | "
            f"{store_name if store_name else '스토어명 없음'} | "
            f"{price if price else '가격 없음'}"
        )

        if product_no:
            log_msg += f" | 상품번호: {product_no}"

        self.logger.info(log_msg)

    async def search_product_rank(
        self,
        keyword: str,
        target_product: Optional[str] = None,
        target_store: Optional[str] = None,
        target_product_no: Optional[str] = None,
        max_pages: int = 10
    ) -> Dict[str, Any]:
        """
        네이버 쇼핑에서 상품 순위 검색 (메인 공개 API)

        지정된 키워드로 네이버 쇼핑을 검색하여 대상 상품의 순위를 찾습니다.
        광고 상품과 일반 상품을 모두 추적하며, 일반 상품 발견 시 즉시 종료합니다.
        (광고는 항상 일반 상품보다 먼저 나오기 때문)

        Args:
            keyword: 검색 키워드 (예: "드럼바", "아식스 테니스화")
            target_product: 찾을 상품명 (부분 일치, 옵션)
                예: "허쉬 드럼바" → "허쉬 드럼바 초콜릿" 매칭
            target_store: 찾을 스토어명 (옵션, 부분 일치)
                상품명 매칭 시 추가 검증용
            target_product_no: 찾을 상품번호 (chnl_prod_no 권장, 옵션)
                가장 정확한 매칭 방법. 상품 URL에서 추출 가능
            max_pages: 검색할 최대 페이지 수 (기본값: 10)
                각 페이지당 약 40개 상품

        Returns:
            Dict[str, Any]: 검색 결과 (4가지 케이스)

            케이스 1 - 일반 상품 발견 (광고 있음):
            {
                'found': True,
                'ad_found': True,
                'keyword': '드럼바',
                'product_name': '...',
                'rank_with_ads': 88,
                'rank_without_ads': 60,
                'page': 3,
                'ad_rank': 26,
                'ad_page': 1
            }

            케이스 2 - 일반 상품만 발견:
            {
                'found': True,
                'ad_found': False,
                'keyword': '드럼바',
                'product_name': '...',
                'rank_with_ads': 88,
                'rank_without_ads': 60,
                'page': 3
            }

            케이스 3 - 광고만 발견:
            {
                'found': False,
                'ad_found': True,
                'keyword': '드럼바',
                'product_name': '...',
                'ad_rank': 26,
                'ad_page': 1
            }

            케이스 4 - 못 찾음:
            {
                'found': False,
                'ad_found': False,
                'keyword': '드럼바',
                'message': '상품을 첫 10 페이지에서 찾지 못함'
            }

        Raises:
            ValueError: target_product와 target_product_no가 모두 None인 경우

        Example:
            >>> bot = NaverRankBot(user_data_dir='./profiles')
            >>> result = await bot.search_product_rank(
            ...     keyword="드럼바",
            ...     target_product_no="82467473814",
            ...     max_pages=5
            ... )
            >>> if result['found']:
            ...     print(f"순위: {result['rank_without_ads']}위")
            ...     if result['ad_found']:
            ...         print(f"광고 순위: {result['ad_rank']}위")

        Note:
            - target_product_no 사용을 강력히 권장 (가장 정확한 매칭 방법)
            - 광고는 항상 일반 상품보다 먼저 나타남
            - 일반 상품 발견 시 즉시 종료 (성능 최적화)
            - 브라우저는 자동으로 시작 및 종료됨
        """
        # 파라미터 검증
        if not target_product and not target_product_no:
            raise ValueError("target_product 또는 target_product_no 중 하나는 반드시 지정해야 합니다")

        try:
            self.logger.info("=== NoDriver 검색 시작 ===")
            self.logger.info(f"키워드: {keyword}")
            if target_product:
                self.logger.info(f"대상 상품명: {target_product}")
            if target_product_no:
                self.logger.info(f"대상 상품번호: {target_product_no}")

            # 브라우저 시작
            self.driver = await self._start_browser()

            # 네이버 홈페이지 열기
            page = await self.driver.get(self.urls.NAVER_HOME)
            await self._navigate_to_naver_home(page)

            # 메인 검색 수행
            try:
                await self._perform_main_search(page, keyword)
                page = await self._navigate_to_shopping_page(page, keyword)
            except Exception as e:
                self.logger.warning(f"검색창 사용 실패: {e}")
                page = await self._navigate_direct_to_shopping(keyword)

            await self.random_wait(3, 5)

            # 상품 로딩 대기
            products_loaded = await self._wait_for_products_to_load(page)
            if not products_loaded:
                self.logger.warning("상품 로딩 타임아웃 - 페이지를 리로드하고 재시도")
                await page.reload()
                await asyncio.sleep(5)

            # 캡차 및 차단 확인
            if not await self._check_for_captcha(page):
                return {"error": "캡차 미해결"}

            if await self._check_for_blocking(page):
                return {"error": "차단됨"}

            # 디버그 모드: 스크린샷 저장
            self.logger.info("검색 결과 분석 중...")
            if self.debug:
                from pathlib import Path
                debug_dir = Path('.debug')
                debug_dir.mkdir(exist_ok=True)
                screenshot_path = debug_dir / "search_result_nodriver.png"
                await page.save_screenshot(str(screenshot_path))
                self.logger.info(f"스크린샷 저장: {screenshot_path}")

            # 검색 수행
            result = await self._search_across_pages(page, keyword, target_product, target_store, target_product_no, max_pages)

            return result

        except Exception as e:
            self.logger.error(f"오류 발생: {e}")
            return {'error': str(e)}

        finally:
            if self.driver:
                await self.close()

    async def _search_across_pages(
        self,
        page: Any,
        keyword: str,
        target_product: Optional[str],
        target_store: Optional[str],
        target_product_no: Optional[str],
        max_pages: int
    ) -> Dict[str, Any]:
        """
        여러 페이지에 걸쳐 상품 검색

        Note: 광고는 항상 일반 상품보다 먼저 나오므로,
              일반 상품을 찾으면 그 시점까지 광고 여부가 확정됨
        """
        rank_with_ads = 0
        rank_without_ads = 0

        # 광고와 일반 상품을 별도로 추적
        ad_product_found = None
        regular_product_found = None

        for page_num in range(1, max_pages + 1):
            self.logger.info(f"\n📄 페이지 {page_num} 검색 중...")

            # 2페이지 이상: 다음 버튼 클릭
            if page_num > 1:
                if not await self._navigate_to_next_page(page):
                    break

            # 페이지 스크롤 및 상품 로드
            await self._scroll_page_to_load_all_products(page)

            # 디버그 모드: 첫 페이지 HTML 저장
            if self.debug and page_num == 1:
                try:
                    from pathlib import Path
                    debug_dir = Path('.debug')
                    debug_dir.mkdir(exist_ok=True)

                    page_html = await page.get_content()
                    html_path = debug_dir / f'page_{page_num}_after_scroll.html'
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(page_html)
                    self.logger.info(f"  페이지 HTML 저장: {html_path}")
                except Exception:
                    pass

            # 상품 추출
            products_info = await self._extract_products_from_page(page)

            if not products_info:
                self.logger.warning("products_info가 None입니다. 빈 리스트로 초기화합니다.")
                products_info = []

            self.logger.info(f"  광고 상품: {len([p for p in products_info if p.get('type') == 'ad'])}개")
            self.logger.info(f"  일반 상품: {len([p for p in products_info if p.get('type') == 'regular'])}개")
            self.logger.info(f"  전체: {len(products_info)}개")

            # 상품 검사 (광고/일반 모두 추적)
            ad_found, regular_found = await self._search_products_in_list(
                products_info,
                rank_with_ads,
                rank_without_ads,
                target_product,
                target_store,
                target_product_no,
                page_num,
                keyword
            )

            # 광고 상품 발견 시 저장
            if ad_found and not ad_product_found:
                ad_product_found = ad_found
                self.logger.info("✅ 광고 상품 발견!")

            # 일반 상품 발견 시 즉시 종료
            # (광고는 항상 일반 상품보다 먼저 나오므로, 이 시점에 광고 여부 확정됨)
            if regular_found:
                regular_product_found = regular_found
                self.logger.info("✅ 일반 상품 발견! 검색 종료")
                break

            # 순위 업데이트
            rank_with_ads += len(products_info)
            rank_without_ads += len([p for p in products_info if not p.get('is_ad', False)])

        # 결과 반환 (4가지 케이스)
        return self._format_search_result(
            keyword,
            ad_product_found,
            regular_product_found,
            max_pages
        )

    async def _search_products_in_list(
        self,
        products_info: List[Dict[str, Any]],
        rank_with_ads_offset: int,
        rank_without_ads_offset: int,
        target_product: Optional[str],
        target_store: Optional[str],
        target_product_no: Optional[str],
        page_num: int,
        keyword: str
    ) -> tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """
        상품 리스트에서 대상 상품 검색 (광고/일반 분리)

        Returns:
            (ad_product_data, regular_product_data) 튜플
        """
        rank_with_ads = rank_with_ads_offset
        rank_without_ads = rank_without_ads_offset

        ad_product_data = None
        regular_product_data = None

        for product_info in products_info:
            rank_with_ads += 1
            is_ad = product_info.get('is_ad', False)
            product_type = product_info.get('type', 'unknown')

            try:
                product_name = product_info.get('title', '')
                store_name = product_info.get('store', '')
                price = product_info.get('price', '')
                product_no = product_info.get('product_no', '')
                nv_mid = product_info.get('nv_mid', '')
                chnl_prod_no = product_info.get('chnl_prod_no', '')

                # 로그 출력 (product_no 포함)
                self._format_product_log(rank_with_ads, product_type, product_name, store_name, price, product_no)

                # 대상 상품 매칭
                if self._match_product(product_name, store_name, product_no, target_product, target_store, target_product_no):
                    current_rank_without_ads = rank_without_ads + (1 if not is_ad else 0)

                    self.logger.info(f"  페이지: {page_num}")
                    self.logger.info(f"  광고 포함 순위: {rank_with_ads}위")

                    product_data = {
                        'keyword': keyword,
                        'product_name': product_name,
                        'store_name': store_name,
                        'product_no': product_no,
                        'nv_mid': nv_mid,
                        'chnl_prod_no': chnl_prod_no,
                        'rank_with_ads': rank_with_ads,
                        'rank_without_ads': current_rank_without_ads if not is_ad else None,
                        'is_ad': is_ad,
                        'product_type': product_type,
                        'price': price,
                        'page': page_num
                    }

                    # 광고 vs 일반 분류
                    if is_ad:
                        self.logger.info("  광고 제외 순위: 광고 상품 (순위 없음)")
                        ad_product_data = product_data
                    else:
                        self.logger.info(f"  광고 제외 순위: {current_rank_without_ads}위")
                        regular_product_data = product_data

                # 광고가 아닌 경우 순위 증가
                if not is_ad:
                    rank_without_ads += 1

            except Exception as e:
                self.logger.debug(f"상품 파싱 오류: {e}")
                continue

        return ad_product_data, regular_product_data

    def _format_search_result(
        self,
        keyword: str,
        ad_product_found: Optional[Dict[str, Any]],
        regular_product_found: Optional[Dict[str, Any]],
        max_pages: int
    ) -> Dict[str, Any]:
        """
        검색 결과를 4가지 케이스에 맞게 포맷팅

        케이스 1: 일반 상품 발견 (광고 있음)
        케이스 2: 일반 상품만 발견
        케이스 3: 광고만 발견
        케이스 4: 아무것도 못 찾음
        """
        # 케이스 1: 일반 상품 발견 (광고 있음)
        if regular_product_found and ad_product_found:
            return {
                'found': True,
                'ad_found': True,
                'keyword': keyword,
                'product_name': regular_product_found['product_name'],
                'store_name': regular_product_found['store_name'],
                'product_no': regular_product_found['product_no'],
                'nv_mid': regular_product_found['nv_mid'],
                'chnl_prod_no': regular_product_found['chnl_prod_no'],
                'rank_with_ads': regular_product_found['rank_with_ads'],
                'rank_without_ads': regular_product_found['rank_without_ads'],
                'price': regular_product_found['price'],
                'page': regular_product_found['page'],
                'ad_rank': ad_product_found['rank_with_ads'],
                'ad_page': ad_product_found['page']
            }

        # 케이스 2: 일반 상품만 발견
        if regular_product_found and not ad_product_found:
            return {
                'found': True,
                'ad_found': False,
                'keyword': keyword,
                'product_name': regular_product_found['product_name'],
                'store_name': regular_product_found['store_name'],
                'product_no': regular_product_found['product_no'],
                'nv_mid': regular_product_found['nv_mid'],
                'chnl_prod_no': regular_product_found['chnl_prod_no'],
                'rank_with_ads': regular_product_found['rank_with_ads'],
                'rank_without_ads': regular_product_found['rank_without_ads'],
                'price': regular_product_found['price'],
                'page': regular_product_found['page']
            }

        # 케이스 3: 광고만 발견
        if ad_product_found and not regular_product_found:
            return {
                'found': False,
                'ad_found': True,
                'keyword': keyword,
                'product_name': ad_product_found['product_name'],
                'store_name': ad_product_found['store_name'],
                'product_no': ad_product_found['product_no'],
                'nv_mid': ad_product_found['nv_mid'],
                'chnl_prod_no': ad_product_found['chnl_prod_no'],
                'price': ad_product_found['price'],
                'ad_rank': ad_product_found['rank_with_ads'],
                'ad_page': ad_product_found['page']
            }

        # 케이스 4: 아무것도 못 찾음
        return {
            'found': False,
            'ad_found': False,
            'keyword': keyword,
            'message': f'상품을 첫 {max_pages} 페이지에서 찾지 못함'
        }

    async def search_multiple_keywords(
        self,
        keywords: List[str],
        target_product: Optional[str] = None,
        target_store: Optional[str] = None,
        target_product_no: Optional[str] = None,
        max_pages: int = 10
    ) -> Dict[str, Any]:
        """
        여러 키워드에서 상품 순위를 한 번에 검색

        Args:
            keywords: 검색할 키워드 리스트
            target_product: 찾을 상품명 (옵션)
            target_store: 찾을 스토어명 (옵션)
            target_product_no: 찾을 상품번호 (옵션)
            max_pages: 각 키워드당 검색할 최대 페이지 수

        Returns:
            {
                'total_searched': 검색한 키워드 수,
                'total_found': 발견한 키워드 수,
                'results': {
                    'keyword1': {...},
                    'keyword2': {...},
                }
            }
        """
        self.logger.info(f"=== 다중 키워드 검색 시작 (총 {len(keywords)}개) ===")

        results = {}
        found_count = 0

        for idx, keyword in enumerate(keywords, 1):
            self.logger.info(f"\n[{idx}/{len(keywords)}] 키워드 검색: {keyword}")

            result = await self.search_product_rank(
                keyword=keyword,
                target_product=target_product,
                target_store=target_store,
                target_product_no=target_product_no,
                max_pages=max_pages
            )

            results[keyword] = result

            if result.get('found'):
                found_count += 1
                self.logger.info(f"✅ {keyword}: {result['rank_with_ads']}위")
            else:
                self.logger.info(f"❌ {keyword}: 미발견")

        self.logger.info(f"\n=== 검색 완료: {found_count}/{len(keywords)} 키워드에서 발견 ===")

        return {
            'total_searched': len(keywords),
            'total_found': found_count,
            'results': results
        }

    async def batch_search(
        self,
        search_requests: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        여러 상품을 여러 키워드로 배치 검색

        Args:
            search_requests: 검색 요청 리스트
                [
                    {
                        'name': '상품1',  # 식별용 이름 (옵션)
                        'keywords': ['키워드1', '키워드2'],
                        'target_product': '상품명',  # 옵션
                        'target_product_no': '123456',  # 옵션
                        'target_store': '스토어명',  # 옵션
                        'max_pages': 3  # 옵션 (기본값 10)
                    },
                    ...
                ]

        Returns:
            {
                'total_requests': 전체 요청 수,
                'completed_requests': 완료된 요청 수,
                'total_keywords': 전체 키워드 수,
                'total_found_keywords': 발견된 키워드 수,
                'results': [
                    {
                        'request_index': 0,
                        'name': '상품1',
                        'total_searched': 2,
                        'total_found': 1,
                        'success_rate': 50.0,
                        'keyword_results': {...}
                    },
                    ...
                ]
            }
        """
        self.logger.info(f"=== 배치 검색 시작 (총 {len(search_requests)}개 요청) ===")

        results = []
        total_keywords = 0
        total_found_keywords = 0
        completed_requests = 0

        for idx, request in enumerate(search_requests, 1):
            # 요청 정보 추출
            name = request.get('name', f'요청_{idx}')
            keywords = request.get('keywords', [])
            target_product = request.get('target_product')
            target_product_no = request.get('target_product_no')
            target_store = request.get('target_store')
            max_pages = request.get('max_pages', 10)

            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"[{idx}/{len(search_requests)}] {name}")
            self.logger.info(f"  키워드: {len(keywords)}개")
            if target_product_no:
                self.logger.info(f"  상품번호: {target_product_no}")
            elif target_product:
                self.logger.info(f"  상품명: {target_product}")
            self.logger.info(f"{'='*60}")

            try:
                # 다중 키워드 검색 실행
                result = await self.search_multiple_keywords(
                    keywords=keywords,
                    target_product=target_product,
                    target_store=target_store,
                    target_product_no=target_product_no,
                    max_pages=max_pages
                )

                # 통계 업데이트
                total_keywords += result['total_searched']
                total_found_keywords += result['total_found']
                completed_requests += 1

                # 성공률 계산
                success_rate = (result['total_found'] / result['total_searched'] * 100) if result['total_searched'] > 0 else 0

                # 결과 저장
                results.append({
                    'request_index': idx - 1,
                    'name': name,
                    'target_product_no': target_product_no,
                    'target_product': target_product,
                    'total_searched': result['total_searched'],
                    'total_found': result['total_found'],
                    'success_rate': success_rate,
                    'keyword_results': result['results']
                })

                self.logger.info(f"✅ {name}: {result['total_found']}/{result['total_searched']} 키워드 발견 ({success_rate:.1f}%)")

            except Exception as e:
                self.logger.error(f"❌ {name} 검색 실패: {e}")
                results.append({
                    'request_index': idx - 1,
                    'name': name,
                    'error': str(e),
                    'total_searched': len(keywords),
                    'total_found': 0,
                    'success_rate': 0.0
                })

        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"배치 검색 완료")
        self.logger.info(f"  완료된 요청: {completed_requests}/{len(search_requests)}")
        self.logger.info(f"  전체 키워드: {total_keywords}개")
        self.logger.info(f"  발견된 키워드: {total_found_keywords}개")
        self.logger.info(f"  전체 발견율: {total_found_keywords/total_keywords*100:.1f}%" if total_keywords > 0 else "  전체 발견율: 0.0%")
        self.logger.info(f"{'='*60}")

        return {
            'total_requests': len(search_requests),
            'completed_requests': completed_requests,
            'total_keywords': total_keywords,
            'total_found_keywords': total_found_keywords,
            'overall_success_rate': (total_found_keywords / total_keywords * 100) if total_keywords > 0 else 0.0,
            'results': results
        }

    async def close(self) -> None:
        """브라우저 종료 및 리소스 정리"""
        if self.driver:
            try:
                # 백그라운드 태스크가 완료될 때까지 짧은 대기
                await asyncio.sleep(0.5)

                stop_result = self.driver.stop()
                if stop_result is not None:
                    await stop_result

                self.logger.info("브라우저 정상 종료")
            except Exception as e:
                # NoDriver의 백그라운드 태스크 정리 중 발생하는 에러는 무시
                # (브라우저는 이미 종료된 상태)
                if "AttributeError" in str(type(e).__name__) or "NoneType" in str(e):
                    self.logger.debug(f"브라우저 종료 완료 (백그라운드 태스크 정리 중 무해한 에러 발생)")
                else:
                    self.logger.warning(f"브라우저 종료 중 오류 (무시됨): {e}")
            finally:
                self.driver = None
