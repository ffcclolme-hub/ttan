import asyncio
import re
import logging
import requests
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

logger = logging.getLogger(__name__)

# Danh sách API bypass miễn phí
BYPASS_APIS = [
    "https://bypass.bio/api/v1/bypass",
    "https://api.bypass.vip/v1/bypass",
    "https://bypass.pm/api/v1/bypass",
]

# Cache đơn giản (lưu kết quả để tránh xử lý lại)
CACHE = {}

async def try_bypass_api(url):
    """Gọi các API bypass miễn phí"""
    for api_url in BYPASS_APIS:
        try:
            logger.info(f"Thử API: {api_url}")
            if "bypass.bio" in api_url:
                resp = requests.get(api_url, params={"url": url}, timeout=20)
            else:
                resp = requests.post(api_url, json={"url": url}, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                # Các API có cấu trúc khác nhau
                destination = data.get("destination") or data.get("url") or data.get("result") or data.get("link")
                if destination and destination != url and destination.startswith("http"):
                    logger.info(f"API {api_url} thành công: {destination}")
                    return destination
                if isinstance(data, str) and data.startswith("http"):
                    return data.strip()
            else:
                logger.warning(f"API {api_url} trả về mã {resp.status_code}")
        except Exception as e:
            logger.warning(f"Lỗi API {api_url}: {e}")
    return None

async def bypass_playwright(url, max_retries=2):
    """Bypass bằng Playwright (click tự động, không captcha)"""
    for attempt in range(max_retries):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True, args=['--no-sandbox'])
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                await page.goto(url, wait_until='networkidle', timeout=45000)

                # 1. Click nút #btn-main (link4m)
                btn = await page.query_selector('#btn-main')
                if btn:
                    await btn.click()
                    await page.wait_for_timeout(3000)
                    await page.wait_for_load_state('networkidle', timeout=15000)
                    final = page.url
                    await browser.close()
                    return final

                # 2. Click các thẻ a có class btn/button
                btns = await page.query_selector_all('a.btn, a.button, input[type="submit"], button')
                for btn in btns:
                    if await btn.is_visible():
                        await btn.click()
                        await page.wait_for_timeout(3000)
                        await page.wait_for_load_state('networkidle', timeout=15000)
                        final = page.url
                        await browser.close()
                        return final

                # 3. Phát hiện window.location trong script
                script_content = await page.evaluate('() => document.documentElement.outerHTML')
                match = re.search(r'window\.location\.href\s*=\s*["\']([^"\']+)["\']', script_content)
                if match:
                    target = match.group(1)
                    if not target.startswith('http'):
                        target = urljoin(url, target)
                    await browser.close()
                    return target

                # 4. Meta refresh
                meta = await page.query_selector('meta[http-equiv="refresh"]')
                if meta:
                    content = await meta.get_attribute('content')
                    if content:
                        match = re.search(r'URL\s*=\s*([^\s;]+)', content, re.IGNORECASE)
                        if match:
                            target = match.group(1)
                            if not target.startswith('http'):
                                target = urljoin(url, target)
                            await browser.close()
                            return target

                final = page.url
                await browser.close()
                return final

        except PlaywrightTimeout:
            logger.warning(f"Playwright timeout lần {attempt+1}")
        except Exception as e:
            logger.error(f"Playwright lỗi: {e}")
    return None

async def bypass_link(url: str) -> str:
    """Hàm chính: thử API trước, sau đó Playwright"""
    # Kiểm tra cache
    if url in CACHE:
        logger.info(f"Lấy từ cache: {CACHE[url]}")
        return CACHE[url]

    # Thử API
    result = await try_bypass_api(url)
    if result and result != url:
        CACHE[url] = result
        return result

    # Thử Playwright
    logger.info("API thất bại, thử Playwright...")
    result = await bypass_playwright(url)
    if result and result != url:
        CACHE[url] = result
        return result

    return None