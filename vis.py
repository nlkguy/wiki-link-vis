
import requests
from bs4 import BeautifulSoup

def getLink(url,count):
    print(URL+str(count))
    
    r = requests.get(URL)
    print(r.status_code)
    soup = BeautifulSoup(r.content, 'html.parser')

    print(soup.title)
    para = soup.find_all('p',limit=5)[1]
    link_soup = BeautifulSoup(str(para), 'html.parser')
    link = link_soup.find("a")

    url = "https://en.wikipedia.org"+str(link.get("href"))
    count-=1
    getLink(url,count)



URL = input("Enter Init wiki : ")
limit = int(input("Enter limit : "))

print(URL+str(limit))

getLink(URL,limit)

