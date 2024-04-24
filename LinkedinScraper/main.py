import asyncio
import math
import os
import re
import time
from typing import List
from urllib.parse import quote_plus
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import pandas as pd
from pathlib import Path
from dataclasses import dataclass
from rich import print
from tqdm import tqdm

from playwrightScraper import Scraper

load_dotenv()


BASE_URL = "https://www.linkedin.com"

@dataclass
class SearchQuery:
    tags: List[str]
    location: str
    start: int = 0
    
    @property
    def url(self):
        tags_str = '+'.join(quote_plus(tag) for tag in self.tags)
        return f'{BASE_URL}/jobs/search/?keywords={tags_str}&location={self.location}&start={str(self.start)}'
    

class LinkedinScraper:
    def __init__(self, params):
        self.params = params
        self.driver = Scraper(params)
        self.jobs_ids = []
        
    async def login(self):
        email = os.getenv("EMAIL")
        password = os.getenv("PASSWORD")
        
        url = f"{BASE_URL}/login"
        await self.driver.get(url)
 
        email_input = self.driver.page.locator('input[name="session_key"]') # type: ignore
        password_input = self.driver.page.locator('input[name="session_password"]')
        login_button = self.driver.page.locator('button[type="submit"]')
        
        await email_input.fill(email)
        await password_input.fill(password)
        await login_button.click()

        await self.driver.page.wait_for_load_state('networkidle')
        
        
    
    async def scrape(self, search: SearchQuery):
        await self.driver.get(search.url)
        print("Scraping ", search.url)
        
        try:
            await self.driver.page.wait_for_selector(".jobs-search-results-list__subtitle")
        except Exception as e:
            print("Locator not found:", e)
            await self.driver.browser.close()
            return
        
        time.sleep(2)
        n_jobs_element = self.driver.page.locator(".jobs-search-results-list__subtitle")
        
        n_jobs_text = await n_jobs_element.text_content()
        n_jobs = int(re.sub(r'\D', '', n_jobs_text))
        n_pages = math.ceil(n_jobs/25)
    
        print("Páginas: ", n_pages)
        for page in range(3):
            new_search = search
            new_search.start = page * 25
            
            await self.driver.get(new_search.url)
            print(f"Jobs found {self.jobs_ids}.", end="\r")
            
            content = await self.driver.page.content()
            jobs_page = self.get_jobs_page(content)
            self.jobs_ids.extend(jobs_page)
        
        return self.jobs_ids

        
    
    def get_jobs_page(self, content):
        
        soup = BeautifulSoup(content, 'html.parser')
        
        jobs_on_page = []
    
        job_postings = soup.find_all('li', {'class': 'jobs-search-results__list-item'})
        for job_posting in job_postings:
            Job_ID = job_posting.get('data-occludable-job-id')
            jobs_on_page.append(Job_ID)        
        return jobs_on_page
        
    

async def main():
    
    search = SearchQuery(
        ["Machine Learning"], 
        "Barcelona"
    )
    
    params = {
        "browser_tag": "ff",
        "headless": True
    }
    
    job = LinkedinScraper(params)
    try:
        await job.login()
        
        jobs = await job.scrape(search)
    finally:
        await job.driver.browser.close()
        
    path = Path(__file__).parent / "id.txt"
    path.write_text('\n'.join(jobs))
        
    


if __name__ == "__main__":
    asyncio.run(main())    