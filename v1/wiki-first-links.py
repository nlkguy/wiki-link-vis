import requests,time
from bs4 import BeautifulSoup


def get_title(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.title.string

def get_first_valid_link(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    first_link = None

    for paragraph in soup.find_all('p'):
        for link in paragraph.find_all('a', href=True):
            href = link['href']
            if not href.startswith('#') and not href.startswith('/wiki/File:'):
                first_link = 'https://en.wikipedia.org' + href
                return first_link

    return first_link

start_link = 'https://en.wikipedia.org/wiki/Cochin_University_of_Science_and_Technology'

iterations = 50

for i in range(iterations):
    print(f'Iteration {i + 1}:')

    current_title = get_title(start_link)
    print(f'Title: {current_title}')

    first_link = get_first_valid_link(start_link)

    if first_link:
        linked_title = get_title(first_link)
        print(f'Linked Title: {linked_title}')

        start_link = first_link
    else:
        print('No more valid links found on this page.')
        break

    time.sleep(2)
