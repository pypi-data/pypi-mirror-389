import asyncio
from enum import Enum
import random
from playwright.async_api import Playwright


class Browser(Enum):
    WEBKIT = "webkit"
    FIREFOX = "firefox"
    CHROME = "chrome"


async def scroll_bottom(
    page, min_scroll=800, max_scroll=1000, min_scrolls=1, max_scrolls=5
):
    scrolls = random.randint(min_scrolls, max_scrolls)
    for _ in range(scrolls):
        scroll_distance = random.randint(min_scroll, max_scroll)
        direction = random.choice([-1, 1])  # 随机选择滚动方向
        await page.mouse.wheel(0, scroll_distance * direction)
        await asyncio.sleep(random.uniform(0.5, 1))

    # 滚动到页面最底端
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
    await asyncio.sleep(random.uniform(0.5, 1))  # 等待一段时间，模拟人类行为
    await page.evaluate("window.scrollTo(0, 0);")


async def get_page(
    p: Playwright,
    url: str,
    engine: Browser = Browser.WEBKIT,
    max_wait: int = 5 * 60 * 1000,
    is_remote: bool = True,
    headless: bool = False,
    playwright_remote_url: str = "",
):
    if not is_remote and not playwright_remote_url:
        raise ValueError("Playwright remote url is empty")
    if not p:
        raise ValueError("Playwright is empty")
    if not url:
        raise ValueError("URL is empty")
    if engine.value == "chrome":
        if is_remote:
            browser = await p.chromium.connect(playwright_remote_url)
        else:
            browser = await p.chromium.launch(headless=headless)
    elif engine.value == "firefox":
        if is_remote:
            browser = await p.firefox.connect(playwright_remote_url)
        else:
            browser = await p.firefox.launch(headless=headless)
    else:
        if is_remote:
            browser = await p.webkit.connect(playwright_remote_url)
        else:
            browser = await p.webkit.launch(headless=headless)
    content = await browser.new_context()
    content.set_default_timeout(max_wait)
    content.set_default_navigation_timeout(max_wait)
    page = await content.new_page()
    await page.goto(url)
    return browser, page, content
