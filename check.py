import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import schedule
import time

def log(message):
    print(message)

async def fetch_url_content(session, url):
    try:
        async with session.get(url, ssl=False) as response:
            return await response.text()
    except Exception as e:
        log(f"ERROR {url}: {e}")
        return None

async def parse_sitemap_urls(sitemap_url):
    async with aiohttp.ClientSession() as session:
        content = await fetch_url_content(session, sitemap_url)
        if not content:
            return []
        try:
            soup = BeautifulSoup(content, 'html.parser')
            return [loc.text for loc in soup.find_all('loc')]
        except Exception as e:
            log(f"SITEMAP PARSE ARROR ({sitemap_url}): {e}")
            return []

async def check_page_status(session, page_url):
    try:
        async with session.get(page_url, ssl=False) as response:
            if response.status != 200:
                log(f"PAGE NOT ACCESSIBLE: {page_url} (Status: {response.status})")
                return False
        return True
    except Exception as e:
        log(f"PAGE NOT ACCESSIBLE: {page_url}: {e}")
        return False

async def process_website(website_url):
    log(f"SITEMAP: {website_url}")
    sitemap_url = urljoin(website_url, '/sitemap.xml')
    sitemap_urls = await parse_sitemap_urls(sitemap_url)

    if not sitemap_urls:
        log(f"NO SITEMAP FOUND: {website_url}")
        return []

    log(f"{len(sitemap_urls)} AMOUNT OF URLS IN SITEMAP: {website_url}")
    async with aiohttp.ClientSession() as session:
        tasks = [check_page_status(session, url) for url in sitemap_urls]
        results = await asyncio.gather(*tasks)

    inaccessible_pages = [url for url, result in zip(sitemap_urls, results) if not result]
    return inaccessible_pages

async def main(file_with_websites):

    with open(file_with_websites, 'r') as file:
        websites = [line.strip() for line in file if line.strip()]

    list_inaccessible_pages = []

    for website in websites:
        inaccessible_pages = await process_website(website)
        list_inaccessible_pages.extend(inaccessible_pages)

    log(f"TOTAL NOT ACCESSIBLE PAGES: {len(list_inaccessible_pages)}")
    for page in list_inaccessible_pages:
        log(f"NOT ACCESSIBLE: {page}")

if __name__ == "__main__":
    file_with_websites = 'websites.txt'
    asyncio.run(main(file_with_websites))
