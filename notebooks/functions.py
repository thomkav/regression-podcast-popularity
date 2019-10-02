from bs4 import BeautifulSoup
import requests
from collections import defaultdict
import json

index_dir = 'https://castbox.fm/'

def collect_category_pods(soup):
    '''
    Create navigational dict of podcast channel as lists on a category page,
    for the top podcasts across all categories, or a single category.
    '''
        
    cat_dict = {}
    pod_rows = soup.find_all('div', class_='coverRow')
    
    for row in pod_rows:
        chan_url = index_dir + row.find('a').get('href')
#         print(chan_url)
        title = row.find(class_='title').text
#         print(title)
        author = row.find(class_='author').text
#         print(author)
#         print('\n')
        cat_dict[title] = {'chan_url': chan_url, 'author': author}
    
    return cat_dict