import asyncio
import re
import logging
import requests
import aiohttp
import json
import base64
import time
import os
from urllib.parse import urlparse, urljoin, parse_qs
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ====== DANH SÁCH API BYPASS (30+ API) ======
BYPASS_APIS = [
    # API chính
    {"url": "https://bypass.bio/api/v1/bypass", "method": "get", "param": "url"},
    {"url": "https://api.bypass.vip/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.pm/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://api.bypass.how/api/v1/bypass", "method": "get", "param": "url"},
    {"url": "https://bypass.xyz/api/v1/bypass", "method": "get", "param": "url"},
    {"url": "https://api.bypass.one/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass-api.com/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://api.bypass.bar/api/v1/bypass", "method": "get", "param": "url"},
    {"url": "https://api.bypass.best/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.it/api/v1/bypass", "method": "get", "param": "url"},
    # API mới bổ sung
    {"url": "https://bypass.icu/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.rip/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.pet/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.cat/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.lol/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.men/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.win/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.plus/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.team/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.cloud/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.net/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.org/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.dev/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.app/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.io/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.run/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.guru/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.zone/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.tech/api/v1/bypass", "method": "post", "param": "url"},
    {"url": "https://bypass.pro/api/v1/bypass", "method": "post", "param": "url"},
]

# ====== CACHE ======
CACHE = {}
CACHE_MAX_SIZE = 2000

# ====== HÀM GỌI API BYPASS ======
async def try_bypass_api(url, session):
    """Gọi tất cả API bypass miễn phí"""
    for api in BYPASS_APIS:
        try:
            logger.info(f"🔄 Thử API: {api['url']}")
            if api['method'] == 'get':
                async with session.get(api['url'], params={api['param']: url}, timeout=15) as resp:
                    if resp.status == 200:
                        try:
                            data = await resp.json()
                        except:
                            data = await resp.text()
                        if isinstance(data, dict):
                            destination = data.get("destination") or data.get("url") or data.get("result") or data.get("link") or data.get("bypassed") or data.get("bypass") or data.get("final_url")
                            if destination and destination != url and destination.startswith("http"):
                                logger.info(f"✅ API {api['url']} thành công: {destination}")
                                return destination
                        elif isinstance(data, str) and data.startswith("http"):
                            return data.strip()
            else:
                async with session.post(api['url'], json={api['param']: url}, timeout=15) as resp:
                    if resp.status == 200:
                        try:
                            data = await resp.json()
                        except:
                            data = await resp.text()
                        if isinstance(data, dict):
                            destination = data.get("destination") or data.get("url") or data.get("result") or data.get("link") or data.get("bypassed") or data.get("bypass") or data.get("final_url")
                            if destination and destination != url and destination.startswith("http"):
                                logger.info(f"✅ API {api['url']} thành công: {destination}")
                                return destination
                        elif isinstance(data, str) and data.startswith("http"):
                            return data.strip()
        except Exception as e:
            logger.warning(f"❌ Lỗi API {api['url']}: {e}")
    return None

# ====== BYPASS BẰNG PLAYWRIGHT (NÂNG CAO) ======
async def bypass_playwright(url, max_retries=3):
    """Bypass bằng Playwright với nhiều chiến thuật"""
    for attempt in range(max_retries):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-setuid-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-web-security',
                        '--disable-features=IsolateOrigins,site-per-process',
                        '--disable-gpu',
                        '--window-size=1920,1080'
                    ]
                )
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={'width': 1920, 'height': 1080},
                    ignore_https_errors=True,
                    java_script_enabled=True
                )
                page = await context.new_page()

                # Bắt redirect
                redirect_url = None
                async def handle_response(response):
                    nonlocal redirect_url
                    if response.status in [301, 302, 303, 307, 308]:
                        location = response.headers.get('location')
                        if location and location.startswith('http'):
                            redirect_url = location
                            logger.info(f"🔀 Redirect: {location}")
                page.on('response', handle_response)

                # Bắt request
                async def handle_request(request):
                    if request.resource_type == 'document':
                        logger.info(f"📄 Request: {request.url}")
                page.on('request', handle_request)

                await page.goto(url, wait_until='networkidle', timeout=45000)
                await page.wait_for_timeout(5000)

                # ====== CHIẾN THUẬT THEO TỪNG LOẠI LINK ======

                # 1. LINK4M
                if 'link4m' in url:
                    btn = await page.query_selector('#btn-main')
                    if btn:
                        await btn.click()
                        await page.wait_for_timeout(3000)
                        await page.wait_for_load_state('networkidle', timeout=10000)
                        final = page.url
                        if final != url:
                            await browser.close()
                            return final

                # 2. ADF.LY
                if 'adf.ly' in url:
                    try:
                        await page.wait_for_selector('#skip_button, .skip-btn, button[class*="skip"]', timeout=15000)
                        btn = await page.query_selector('#skip_button, .skip-btn, button[class*="skip"]')
                        if btn:
                            await btn.click()
                            await page.wait_for_timeout(3000)
                            await page.wait_for_load_state('networkidle', timeout=10000)
                            final = page.url
                            if final != url:
                                await browser.close()
                                return final
                    except:
                        pass

                # 3. OUO.IO
                if 'ouo.io' in url:
                    btn = await page.query_selector('button:has-text("Get Link"), a:has-text("Get Link")')
                    if btn:
                        await btn.click()
                        await page.wait_for_timeout(3000)
                        await page.wait_for_load_state('networkidle', timeout=10000)
                        final = page.url
                        if final != url:
                            await browser.close()
                            return final

                # 4. SH.ST
                if 'sh.st' in url:
                    try:
                        await page.wait_for_selector('#download-link, .download-link, a[class*="download"]', timeout=15000)
                        btn = await page.query_selector('#download-link, .download-link, a[class*="download"]')
                        if btn:
                            await btn.click()
                            await page.wait_for_timeout(3000)
                            await page.wait_for_load_state('networkidle', timeout=10000)
                            final = page.url
                            if final != url:
                                await browser.close()
                                return final
                    except:
                        pass

                # 5. SHORTE.ST
                if 'shorte.st' in url:
                    try:
                        await page.wait_for_selector('#main-btn, .main-btn, a[class*="main"]', timeout=15000)
                        btn = await page.query_selector('#main-btn, .main-btn, a[class*="main"]')
                        if btn:
                            await btn.click()
                            await page.wait_for_timeout(3000)
                            await page.wait_for_load_state('networkidle', timeout=10000)
                            final = page.url
                            if final != url:
                                await browser.close()
                                return final
                    except:
                        pass

                # ====== TÌM VÀ CLICK NÚT (TỔNG QUÁT) ======
                button_texts = [
                    'Continue', 'Skip', 'Get Link', 'Proceed', 'Go to Link',
                    'Show Link', 'View Link', 'Unlock', 'Free Access',
                    'Bypass', 'Click here', 'Skip Ad', 'Next', '->',
                    'T?p t?c', 'Ti?p t?c', 'B? qua', 'L?y link', 'Xem link',
                    'Download', 'T?i xu?ng', 'Link', 'Here', 'Go'
                ]
                for text in button_texts:
                    try:
                        btn = await page.query_selector(f'button:has-text("{text}"), a:has-text("{text}")')
                        if btn and await btn.is_visible():
                            await btn.click()
                            await page.wait_for_timeout(3000)
                            await page.wait_for_load_state('networkidle', timeout=10000)
                            final = page.url
                            if final != url:
                                await browser.close()
                                return final
                    except:
                        pass

                # ====== CLICK BẰNG CSS SELECTOR ======
                selectors = [
                    'a.btn', 'a.button', 'input[type="submit"]', 'button',
                    'a[role="button"]', 'a[class*="btn"]', 'button[class*="btn"]',
                    '.skip-button', '#skip-btn', '.next-btn', '.go-btn',
                    '.get-link-btn', '#get-link', '.bypass-btn', '.download-btn',
                    '.continue-btn', '.proceed-btn', '.show-link-btn'
                ]
                for selector in selectors:
                    try:
                        btns = await page.query_selector_all(selector)
                        for btn in btns:
                            if await btn.is_visible() and await btn.is_enabled():
                                await btn.click()
                                await page.wait_for_timeout(3000)
                                await page.wait_for_load_state('networkidle', timeout=10000)
                                final = page.url
                                if final != url:
                                    await browser.close()
                                    return final
                    except:
                        pass

                # ====== XỬ LÝ IFRAME ======
                try:
                    iframes = await page.query_selector_all('iframe')
                    for iframe in iframes:
                        try:
                            src = await iframe.get_attribute('src')
                            if src and any(x in src for x in ['adf.ly', 'ouo.io', 'link4m', 'sh.st', 'shorte.st']):
                                frame = await iframe.content_frame()
                                if frame:
                                    btns = await frame.query_selector_all('button, a.btn, input[type="submit"]')
                                    for btn in btns:
                                        if await btn.is_visible():
                                            await btn.click()
                                            await page.wait_for_timeout(3000)
                                            await page.wait_for_load_state('networkidle', timeout=10000)
                                            final = page.url
                                            if final != url:
                                                await browser.close()
                                                return final
                        except:
                            pass
                except:
                    pass

                # ====== PHÁT HIỆN SCRIPT REDIRECT ======
                try:
                    script_content = await page.evaluate('() => document.documentElement.outerHTML')
                    patterns = [
                        r'window\.location\.href\s*=\s*["\']([^"\']+)["\']',
                        r'window\.location\.replace\s*\(\s*["\']([^"\']+)["\']',
                        r'window\.location\.assign\s*\(\s*["\']([^"\']+)["\']',
                        r'setTimeout\s*\(\s*function\s*\(\s*\)\s*\{\s*window\.location\.href\s*=\s*["\']([^"\']+)["\']',
                        r'location\.href\s*=\s*["\']([^"\']+)["\']',
                        r'var\s+url\s*=\s*["\']([^"\']+)["\']',
                        r'const\s+url\s*=\s*["\']([^"\']+)["\']',
                        r'let\s+url\s*=\s*["\']([^"\']+)["\']',
                        r'window\.open\s*\(\s*["\']([^"\']+)["\']'
                    ]
                    for pattern in patterns:
                        match = re.search(pattern, script_content)
                        if match:
                            target = match.group(1)
                            if not target.startswith('http'):
                                target = urljoin(url, target)
                            if target != url:
                                await browser.close()
                                return target
                except:
                    pass

                # ====== META REFRESH ======
                try:
                    meta = await page.query_selector('meta[http-equiv="refresh"]')
                    if meta:
                        content = await meta.get_attribute('content')
                        if content:
                            match = re.search(r'URL\s*=\s*([^\s;]+)', content, re.IGNORECASE)
                            if match:
                                target = match.group(1)
                                if not target.startswith('http'):
                                    target = urljoin(url, target)
                                if target != url:
                                    await browser.close()
                                    return target
                except:
                    pass

                # ====== LẤY URL CUỐI ======
                final = page.url
                await browser.close()

                if redirect_url and redirect_url != url:
                    return redirect_url
                if final != url:
                    return final

                return None

        except PlaywrightTimeout:
            logger.warning(f"⏱️ Playwright timeout lần {attempt+1}")
        except Exception as e:
            logger.error(f"❌ Playwright lỗi: {e}")
            await asyncio.sleep(1)
    return None

# ====== BYPASS BẰNG SELENIUM (FALLBACK) ======
def bypass_selenium(url):
    """Bypass bằng Selenium (fallback khi Playwright thất bại)"""
    try:
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        time.sleep(5)

        # Tìm và click nút
        try:
            btn = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, '#btn-main, .btn, a.btn, button, .skip-btn, #skip-btn'))
            )
            btn.click()
            time.sleep(3)
        except:
            pass

        # Tìm link cuối
        final_url = driver.current_url
        driver.quit()

        if final_url != url:
            return final_url
        return None
    except Exception as e:
        logger.error(f"❌ Selenium lỗi: {e}")
        return None

# ====== BYPASS BẰNG REQUESTS ĐƠN GIẢN ======
def bypass_requests(url):
    """Bypass đơn giản bằng requests"""
    try:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        resp = session.get(url, allow_redirects=True, timeout=30)
        if resp.url != url:
            return resp.url
        return None
    except:
        return None

# ====== HÀM CHÍNH ======
async def bypass_link(url: str) -> str:
    """Bypass link rút gọn - Hàm chính với nhiều lớp fallback"""
    # Kiểm tra cache
    if url in CACHE:
        logger.info(f"📦 Cache: {CACHE[url]}")
        return CACHE[url]

    logger.info(f"🔍 Bắt đầu bypass: {url}")

    # Lớp 1: Thử API
    try:
        async with aiohttp.ClientSession() as session:
            result = await try_bypass_api(url, session)
            if result and result != url:
                CACHE[url] = result
                if len(CACHE) > CACHE_MAX_SIZE:
                    CACHE.pop(next(iter(CACHE)))
                return result
    except Exception as e:
        logger.error(f"Lỗi API: {e}")

    # Lớp 2: Thử Playwright
    try:
        logger.info("🌐 Thử Playwright...")
        result = await bypass_playwright(url)
        if result and result != url:
            CACHE[url] = result
            if len(CACHE) > CACHE_MAX_SIZE:
                CACHE.pop(next(iter(CACHE)))
            return result
    except Exception as e:
        logger.error(f"Lỗi Playwright: {e}")

    # Lớp 3: Thử Selenium (chạy trong thread riêng)
    try:
        logger.info("🌐 Thử Selenium...")
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, bypass_selenium, url)
        if result and result != url:
            CACHE[url] = result
            if len(CACHE) > CACHE_MAX_SIZE:
                CACHE.pop(next(iter(CACHE)))
            return result
    except Exception as e:
        logger.error(f"Lỗi Selenium: {e}")

    # Lớp 4: Thử Requests (cuối cùng)
    try:
        logger.info("🌐 Thử Requests...")
        result = bypass_requests(url)
        if result and result != url:
            CACHE[url] = result
            if len(CACHE) > CACHE_MAX_SIZE:
                CACHE.pop(next(iter(CACHE)))
            return result
    except Exception as e:
        logger.error(f"Lỗi Requests: {e}")

    return None