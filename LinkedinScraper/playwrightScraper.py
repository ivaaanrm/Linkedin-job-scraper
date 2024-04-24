import asyncio
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright
from playwright.async_api import Page
from bs4 import BeautifulSoup
from dataclasses import dataclass
import time


class Scraper:
    def __init__(self, params):
        self.params = params
        self.playwright = None
        self.browser = None
        self.page = None
        self.browser_tag = self.params['browser_tag']
                
    
    async def setup(self):
        self.playwright = await async_playwright().start()
        if self.browser_tag == "ff":
            self.browser = await self.playwright.firefox.launch(headless=self.params['headless'])
        elif self.browser_tag == "wk":
            self.browser = await self.playwright.webkit.launch(headless=self.params['headless'])
        else:
            self.browser = await self.playwright.chromium.launch(headless=self.params['headless'])
        
        self.page = await self.browser.new_page()
    
    async def get(self, url):
        if not self.page:
            print("Initializing driver...")
            await self.setup()
        try:
            await self.page.goto(url)
            # await self.page.wait_for_load_state(state='networkidle')
        except Exception as e:
            print(f"Error while navigating to URL: {url}. Error: {e}")
            return 404
            
    
    async def get_href(self, xpath: str):
        element = self.page.locator(f'xpath={xpath}')
        if element:
            href = await element.get_attribute('href')
            return href
        else:
            return None
        
    
    async def scroll_to_bottom(self, sleep_time=120):
        last_height = self.page.evaluate('() => document.body.scrollHeight')
        while True:
            self.page.evaluate('() => window.scrollTo(0, document.body.scrollHeight);')
            new_height = self.page.evaluate('() => document.body.scrollHeight')
            if new_height == last_height:
                break
            last_height = new_height

            self.page.wait_for_timeout(sleep_time)