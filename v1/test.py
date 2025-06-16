
import requests
from bs4 import BeautifulSoup

next = ""

def linkinator(URL):
    global next
    r = requests.get(URL)
    soup = BeautifulSoup(r.content, 'html.parser')
    print(soup.title)
    para = soup.find_all('p')[1]
    link_soup = BeautifulSoup(str(para), 'html.parser')
    link = link_soup.find("a")
    tail = str(link.get("href"))
    url = "https://en.wikipedia.org/"+tail
    print(url)
    next = url


URL = "https://en.wikipedia.org/wiki/Baljuna_Covenant"

for i in range(0,100):
    linkinator(URL)
    URL = next


