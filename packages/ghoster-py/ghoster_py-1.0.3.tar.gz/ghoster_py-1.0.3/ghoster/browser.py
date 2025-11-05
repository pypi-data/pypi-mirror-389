import asyncio
import random
from playwright.async_api import async_playwright, Page
from playwright_stealth import stealth_async

from .motion import generate_bezier_path

class GhostBrowser:
    """
    The main class to manage a stealth browser instance.
    It launches a stealth-configured browser and provides a context for creating pages.
    Designed to be used as an async context manager (`async with`).
    """
    def __init__(self, launch_options=None):
        self.launch_options = launch_options or {}
        self._playwright = None
        self.browser = None

    async def __aenter__(self):
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(**self.launch_options)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def new_page(self, context_options=None):
        """
        Creates a new stealth-configured browser page.
        """
        if not self.browser:
            raise Exception("Browser not launched. Use 'async with GhostBrowser() as ghost:'.")
        
        context_options = context_options or {}
        context = await self.browser.new_context(**context_options)
        await stealth_async(context)
        
        page = await context.new_page()
        return GhostPage(page)


class GhostPage:
    """A wrapper around Playwright's Page class to add human-like interaction methods."""

    def __init__(self, page: Page):
        self.page = page
        self._current_mouse_pos = {"x": 0, "y": 0}

    async def goto(self, url: str, **kwargs):
        """Navigates to a URL and resets the mouse position."""
        self._current_mouse_pos = {"x": 0, "y": 0}
        if 'waitUntil' not in kwargs:
            kwargs['waitUntil'] = 'domcontentloaded'
        return await self.page.goto(url, **kwargs)

    async def screenshot(self, **kwargs):
        """Takes a screenshot of the page."""
        return await self.page.screenshot(**kwargs)

    async def human_move(self, selector: str):
        """Moves the mouse over an element in a human-like curve."""
        element = self.page.locator(selector)
        box = await element.bounding_box()
        if not box:
            raise Exception(f"Could not find element with selector: {selector}")

        start_pos = self._current_mouse_pos

        target_pos = {
            "x": box["x"] + box["width"] * (0.2 + random.random() * 0.6),
            "y": box["y"] + box["height"] * (0.2 + random.random() * 0.6),
        }

        path = generate_bezier_path(start_pos, target_pos, steps=20)

        for point in path:
            await self.page.mouse.move(point["x"], point["y"])
            self._current_mouse_pos = point
            await asyncio.sleep(random.uniform(0.01, 0.02))

    async def human_click(self, selector: str):
        """Moves to and clicks an element in a human-like way."""
        await self.human_move(selector)
        await asyncio.sleep(random.uniform(0.2, 0.4))
        await self.page.locator(selector).click()

    async def human_type(self, selector: str, text: str):
        """Moves to, clicks, and types text into an element in a human-like way."""
        await self.human_move(selector)
        await self.page.locator(selector).click()
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        for char in text:
            await self.page.keyboard.type(char)
            await asyncio.sleep(random.uniform(0.09, 0.15))

    # We will add other methods like capture_blob and save_session here later.

    def __getattr__(self, name):
        """
        Pass-through for any other methods or properties of the original Page object.
        This makes our GhostPage wrapper transparent.
        """
        return getattr(self.page, name)