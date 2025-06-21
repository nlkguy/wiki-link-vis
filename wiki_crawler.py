# crawling functions 

import asyncio
import httpx
import json
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin


# todo - options for other lanfuages

BASE_URL = "https://en.wikipedia.org"

# thiese pages mess up crawlee
BLACKLIST_PREFIXES = (
    "/wiki/Help:", "/wiki/Special:", "/wiki/File:", "/wiki/Category:",
    "/wiki/Talk:", "/wiki/User:", "/wiki/Template:", "/wiki/Portal:", "/wiki/Wikipedia:", "/wiki/Main_Page"
)

async def extract_first_valid_link(page_url):
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(page_url)
            soup = BeautifulSoup(resp.text, "html.parser")
            for p in soup.select("p"):
                for link in p.find_all("a", href=True):
                    href = link["href"]
                    if href.startswith("/wiki/") and not any(href.startswith(prefix) for prefix in BLACKLIST_PREFIXES):
                        return urljoin(BASE_URL, href)
        except Exception as e:
            print(f"Error: {e}")
    return None

#crawl chain recursively call above func
# todo - make settings file
#      - max points - specify
#      - resume crawlee
#      - if first link is loop - go to second link


#      - make the philosophy STOPPEE optional


async def crawl_chain(start_title, max_steps=1000):
    visited = []
    current = urljoin(BASE_URL, f"/wiki/{start_title}")

    merge_points = []
    # todo to do the to mege points list

    for _ in range(max_steps):
        if current in visited:
            visited.append(current)
            return visited
        

        visited.append(current)

        if current.endswith("/Philosophy"):
            return visited

        next_link = await extract_first_valid_link(current)
        if not next_link:
            return visited + ["[Dead End]"]

        current = next_link

    return visited + ["[Max Depth Reached]"]