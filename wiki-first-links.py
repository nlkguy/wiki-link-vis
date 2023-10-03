import requests
from bs4 import BeautifulSoup
import time

# Function to get the title of a Wikipedia page
def get_title(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    return soup.title.string

# Function to find the first valid hyperlink on a Wikipedia page
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

# Define the Wikipedia link to start from
start_link = 'https://en.wikipedia.org/wiki/Cochin_University_of_Science_and_Technology'

# Define the number of iterations
iterations = 50

for i in range(iterations):
    print(f'Iteration {i + 1}:')

    # Get and print the title of the current page
    current_title = get_title(start_link)
    print(f'Title: {current_title}')

    # Get the first valid link on the current page
    first_link = get_first_valid_link(start_link)

    if first_link:
        # Get and print the title of the linked page
        linked_title = get_title(first_link)
        print(f'Linked Title: {linked_title}')

        # Set the start link for the next iteration to the linked page
        start_link = first_link
    else:
        print('No more valid links found on this page.')
        break

    # Sleep for a short time to avoid overwhelming Wikipedia's servers
    time.sleep(2)
