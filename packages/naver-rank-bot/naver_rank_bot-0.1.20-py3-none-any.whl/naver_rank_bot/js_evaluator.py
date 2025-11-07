#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JavaScript 실행 및 응답 처리 모듈

NoDriver를 통한 JavaScript evaluation과 응답 변환 기능을 제공합니다.
"""

from typing import Any


class JSEvaluator:
    """
    JavaScript 실행 템플릿 관리 클래스

    NoDriver의 네이티브 요소 찾기가 동적 콘텐츠에서 불안정하기 때문에,
    JavaScript evaluation을 통해 DOM을 직접 조작합니다.

    Methods:
        get_product_count(): 페이지의 상품 개수 카운트
        extract_all_products(): 모든 상품 정보 추출 (제목, 가격, 상품번호 등)
        scroll_to_bottom(): 페이지 하단으로 스크롤
        get_body_height(): 페이지 높이 측정

    Note:
        모든 메서드는 JavaScript 코드 문자열을 반환합니다.
        실제 실행은 page.evaluate()를 통해 이루어집니다.
    """

    @staticmethod
    def get_product_count() -> str:
        """
        페이지의 상품 개수 카운트 스크립트

        Returns:
            str: 모든 상품 타입(광고, 슈퍼적립, 일반)을 포함한 총 개수를 반환하는 JavaScript

        Example:
            >>> count = await page.evaluate(js.get_product_count())
            >>> print(f"Found {count} products")
        """
        return """
            (() => {
                const products = document.querySelectorAll("div[class*='product_item__'], div[class*='adProduct_item__'], div[class*='superSavingProduct_item__']");
                return products.length;
            })()
        """

    @staticmethod
    def extract_all_products() -> str:
        """
        모든 상품 정보 추출 스크립트 (가장 중요한 메서드)

        DOM에서 모든 상품을 순회하며 다음 정보를 추출합니다:
        - 상품명 (title)
        - 스토어명 (store)
        - 가격 (price)
        - 상품번호 (product_no, chnl_prod_no) - data-shp-contents-dtl 속성에서 추출
        - 상품 타입 (type: 'ad', 'super', 'regular')
        - 광고 여부 (is_ad: true/false)

        Returns:
            str: 상품 정보 배열을 반환하는 JavaScript 코드
                [{title, store, price, product_no, chnl_prod_no, type, is_ad}, ...]

        Note:
            - DOM 순서를 유지하여 정확한 순위를 계산합니다
            - product_no는 chnl_prod_no를 우선 사용 (가장 정확)
            - HTML 엔티티 디코딩 처리 (&quot; → ")
            - 광고(ad)와 슈퍼적립(super)은 모두 is_ad=true로 분류

        Example:
            >>> products = await page.evaluate(js.extract_all_products())
            >>> products = unwrap_nodriver_response(products)
            >>> for p in products:
            ...     print(f"{p['title']} - {p['type']}")
        """
        return r"""
            (() => {
                const products = [];
                const allProducts = document.querySelectorAll("div[class*='product_item__'], div[class*='adProduct_item__'], div[class*='superSavingProduct_item__']");

                for (let i = 0; i < allProducts.length; i++) {
                    const product = allProducts[i];
                    const isAd = product.className.includes('adProduct_item__');
                    const isSuperSaving = product.className.includes('superSavingProduct_item__');

                    let titleElem, storeElem, priceElem, linkElem;
                    let productType, isAdType;

                    if (isAd) {
                        productType = 'ad';
                        isAdType = true;
                        linkElem = product.querySelector("a[class*='adProduct_link__']");
                        titleElem = linkElem;
                        storeElem = product.querySelector("span[class*='product_mall_name__'], a[class*='adProduct_mall__'], a[class*='product_mall__']");
                        priceElem = product.querySelector("span[class*='price_num__'], strong[class*='adProduct_price__'] span.price");
                    } else if (isSuperSaving) {
                        productType = 'super';
                        isAdType = true;
                        linkElem = product.querySelector("a[class*='superSavingProduct_link__']");
                        titleElem = linkElem;
                        storeElem = product.querySelector("span[class*='product_mall_name__'], a[class*='product_mall__']");
                        priceElem = product.querySelector("span[class*='price_num__']");
                    } else {
                        productType = 'regular';
                        isAdType = false;
                        linkElem = product.querySelector("a[class*='product_link__']");
                        titleElem = linkElem;
                        storeElem = product.querySelector("span[class*='product_mall_name__'], a[class*='product_mall__'], div[class*='product_mall__'] a");
                        priceElem = product.querySelector("span[class*='price_num__']");
                    }

                    // Product No 추출 (chnl_prod_no만 사용)
                    let chnlProdNo = '';
                    let productNo = '';

                    // data-shp-contents-dtl에서 추출 (linkElem 우선, 없으면 product에서)
                    let contentsDtl = linkElem ? linkElem.getAttribute('data-shp-contents-dtl') : null;
                    if (!contentsDtl) {
                        contentsDtl = product.getAttribute('data-shp-contents-dtl');
                    }

                    if (contentsDtl) {
                        try {
                            // HTML 엔티티 디코딩 (&quot; -> ")
                            const decodedDtl = contentsDtl.replace(/&quot;/g, '"');
                            const dtlData = JSON.parse(decodedDtl);
                            const chnlProdNoObj = dtlData.find(item => item.key === 'chnl_prod_no');
                            if (chnlProdNoObj) chnlProdNo = chnlProdNoObj.value;
                        } catch(e) {
                            console.log('Failed to parse data-shp-contents-dtl:', e.message);
                        }
                    }

                    // URL에서 추출 (대체 방법)
                    if (!chnlProdNo && linkElem) {
                        const href = linkElem.href || '';
                        // chnl_prod_no 추출
                        const chnlMatch = href.match(/[?&]chnl_prod_no=(\d+)/i);
                        if (chnlMatch) chnlProdNo = chnlMatch[1];
                    }

                    // chnl_prod_no만 사용
                    productNo = chnlProdNo || '';

                    // 스토어명 추출 (여러 방법 시도)
                    let storeName = '';
                    if (storeElem) {
                        storeName = (storeElem.innerText || storeElem.textContent || '').trim();
                    }

                    // storeElem이 없거나 비어있으면 추가 셀렉터 시도
                    if (!storeName) {
                        const storeSelectors = [
                            "a[class*='product_mall__']",
                            "div[class*='product_mall__'] a",
                            "span[class*='mall']",
                            "a[href*='smartstore.naver.com']"
                        ];

                        for (const selector of storeSelectors) {
                            const elem = product.querySelector(selector);
                            if (elem) {
                                storeName = (elem.innerText || elem.textContent || '').trim();
                                if (storeName) break;
                            }
                        }
                    }

                    products.push({
                        type: productType,
                        is_ad: isAdType,
                        title: titleElem ? (titleElem.title || titleElem.innerText || '').trim() : '',
                        store: storeName,
                        price: priceElem ? (priceElem.innerText || priceElem.textContent || '').trim() : '',
                        product_no: productNo,
                        chnl_prod_no: chnlProdNo,
                        index: i
                    });
                }

                return products;
            })()
        """

    @staticmethod
    def scroll_to_bottom() -> str:
        """페이지 하단 스크롤 스크립트"""
        return "window.scrollTo(0, document.body.scrollHeight)"

    @staticmethod
    def get_body_height() -> str:
        """페이지 높이 조회 스크립트"""
        return "document.body.scrollHeight"


def unwrap_nodriver_response(data: Any) -> Any:
    """
    NoDriver의 특수 응답 형식을 일반 Python 객체로 변환

    NoDriver의 page.evaluate() 결과는 특수한 중첩 구조로 반환됩니다:
    [['key', {'type': 'string', 'value': 'actual_value'}], ...]

    이 함수는 이를 일반적인 Python dict로 변환합니다:
    {'key': 'actual_value', ...}

    Args:
        data: NoDriver로부터 받은 응답 (list, dict, 또는 primitive)

    Returns:
        변환된 Python 객체 (dict, list, str, int 등)

    Example:
        >>> raw_result = await page.evaluate(js.extract_all_products())
        >>> products = unwrap_nodriver_response(raw_result)
        >>> print(products[0]['title'])  # 이제 정상적으로 접근 가능

    Note:
        모든 JavaScript evaluation 결과에 이 함수를 적용해야 합니다.
        그렇지 않으면 [['key', {...}]] 형식으로 데이터에 접근할 수 없습니다.
    """
    if isinstance(data, list):
        if len(data) > 0 and isinstance(data[0], list) and len(data[0]) == 2:
            # [['key', {'type': 'string', 'value': 'val'}], ...] 형식
            result = {}
            for item in data:
                if isinstance(item, list) and len(item) == 2:
                    key = item[0]
                    val = item[1]
                    if isinstance(val, dict) and 'value' in val:
                        result[key] = unwrap_nodriver_response(val['value'])
                    else:
                        result[key] = val
            return result
        else:
            # 일반 리스트
            return [unwrap_nodriver_response(item) for item in data]
    elif isinstance(data, dict):
        if 'value' in data and 'type' in data:
            # {'type': 'type', 'value': val} 형식
            return unwrap_nodriver_response(data['value'])
        else:
            # 일반 딕셔너리
            return {k: unwrap_nodriver_response(v) for k, v in data.items()}
    else:
        return data
