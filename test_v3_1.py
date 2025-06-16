# import wikipediaapi
# meh , the api seems a bit overkill for dees

import requests
from bs4 import BeautifulSoup as bs
import sys


blacklist = [
    "/wiki/Special:",
    "/wiki/File:",
    "/wiki/Help:",
    "/wiki/Category:",
    "/wiki/Portal:",
    "/wiki/Talk:",
    "/wiki/User:",
    "/wiki/Wikimedia:",
    "/wiki/Template:",
    "/wiki/Book:",
    "/wiki/MediaWiki:",
    "/wiki/Index:",
    "/wiki/Project:",
    "/wiki/Main_Page",
]



def get_links(url):
    response = requests.get(url)
    soup = bs(response.text, "html.parser")
    links = soup.find_all("a", href=True)
    seed = url.split("wiki/")[-1]
    blacklist.append(f"/wiki/{seed}")

    valid_links = []
    for link in links:
        href = link.get("href")
        if ":" not in href and href.startswith("/wiki/") and not href.startswith("/wiki/Special:"):
            if href not in blacklist:
                valid_links.append(f"https://en.wikipedia.org{href}")

    return valid_links



def main():
    """
    Main function to fetch and print links from a Wikipedia page.
    """
    url = "https://en.wikipedia.org/wiki/Main_Page"
    # url = "https://en.wikipedia.org/wiki/Emmy_Noether"
    links = get_links(url)
    
    x = links[0]
    count = 0
    while(x):
        
        print(f"Step {count+1}: {x}")
        if x == "https://en.wikipedia.org/wiki/Philosophy":
            print("Reached Philosophy page, stopping.")
            break

        links = get_links(x)
        if not links:
            break
        x = links[0]
        count += 1
    print(f"Final link after {count} steps: {x}")
    """
    for i in range(int(sys.argv[1])):
        print(f"Step {i+1}: {x}")
        x = get_links(x)[0]
    """



if __name__ == "__main__":
    main() 


"""
# url = "https://en.wikipedia.org/wiki/Main_Page"
url = "https://en.wikipedia.org/wiki/Emmy_Noether"
response = requests.get(url)
soup = bs(response.text, "html.parser")
links = soup.find_all("a", href=True)

print("Total links:", len(links))


seed = url.split("wiki/")[-1]
blacklist.append(f"/wiki/{seed}")
for link in links[:1000]:
    href = link.get("href")
    if ":" not in href and href.startswith("/wiki/") and href.startswith("/wiki/") and not href.startswith("/wiki/Special:"):
        if href not in blacklist:
            print(f"https://en.wikipedia.org{href}")
            return f"https://en.wikipedia.org{href}"



"""