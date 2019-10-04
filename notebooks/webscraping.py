from bs4 import BeautifulSoup
import requests

from collections import defaultdict
import json

import sys
import time, os
import datetime as dt
import pandas as pd

import sys
import importlib

import re

# webdriver imports
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
chromedriver = "/Applications/chromedriver" # path to the chromedriver executable
os.environ["webdriver.chrome.driver"] = chromedriver

index_dir = 'https://castbox.fm'

def scan_for_valid_category_category_urls():
    '''

    Scan the Castbox directory for unique category pages that
    don't return the "Top Shows" directory, which is the default.

    '''


    # Create a list of possible category pages by forming candidate URLs.
    cat_candidates = [] 
    for i in range(10000, 10251, 1):
        url = 'https://castbox.fm/categories/' + str(i) + '?country=us'
        cat_candidates += [url]

    valid_cats = []

    # Request page source for each url and check its category.
    for url in cat_candidates:

        soup = BeautifulSoup(requests.get(url).text)

        # This div displays the 'category' of the directory.
        category_name = soup.find(class_='guru-breadcrumb-item active').text

        if category_name != 'Top Shows':
            valid_cats += [url]

        time.sleep(0.2)

    return valid_cats


def get_category_source(url, dr):
    '''
    Gets the source code of a category page using the scroll_bottom method.
    '''


    def scroll_bottom():
        '''

        Thwart infinite scroll. Takes driver as input
        Thanks to @ Matthew Eungoo Lee starting me off with this snippet.

        '''

        # Load Entire Page by Scrolling to the Bottom
        SCROLL_PAUSE_TIME = 2# Scroll to very Bottom to Load All
        last_height = dr.execute_script("return document.body.scrollHeight")# Get scroll height
        while True:    
            dr.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            ) # Scroll down to bottom

            time.sleep(1) # Wait a sec

            # Go back up, to trigger infinite scroll
            dr.execute_script(
                "window.scrollTo(0, 0);"
            ) # Scroll down to bottom

            time.sleep(1) # Wait a sec

            # Then back down
            dr.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            ) # Scroll down to bottom

            time.sleep(SCROLL_PAUSE_TIME) # Wait to load page

            new_height = dr.execute_script(
                "return document.body.scrollHeight"
            )# Calculate new scroll height and compare with last scroll height
            if new_height == last_height:
                return True
            last_height = new_height

            return None


    # Navigate to the webpage
    # dr.set_window_rect(*window_rect)
    dr.get(url)

    # close annoying cookie verification
    try:
        dr.find_element_by_class_name('allow').click()
    except:
        # sometimes the cookie doesn't appear
        pass

    scroll_bottom()

    return dr.page_source


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


def scrape_full_category_page(url, dr):
    '''

    Crawl through the entirety of a category page.

    Takes the URL of the category page,
    and the web driver.

    Return the scraped category listing,
    as well as the name of the category.

    '''


    # open page properly and get full source
    source = get_category_source(url, dr)
    time.sleep(0.2)

    # grab entire listing as dictionary
    soup = BeautifulSoup(source, 'lxml')
    category_dict = collect_category_pods(soup)

    # page category
    category_name = soup.find(class_='guru-breadcrumb-item active').text

    return category_name, category_dict


def process_channel_soup(chan_url, html):
    '''

    Build features from scraped html of url.
    Use on a single channel's page.

    Return a dictionary of features for that channel.

    '''

    f = {}

    soup = BeautifulSoup(html, 'lxml')

    ##### Individual Channel Features #####

    # channel title for validation
    f['title'] = soup.find(class_='ch_feed_info_title').find('span').text

    f['chan_url'] = chan_url
    
    print('scraping: ', f['title'])
    
    comment_el = re.sub('[\(\)]', '', soup.find(class_='commentList-title').find('span').text.split('\xa0')[-1])
    
    if len(comment_el) == 0:
        num_comments = '0'
    else:
        num_comments = int(comment_el)
#     print(num_comments)

    f['num_comments'] = int(num_comments)

    # channel author
    f['author'] = soup.find(class_='author').text.split(':')[-1].strip().replace(',','')
    
    f['description'] = soup.find(class_='des-con').text.split(':')[-1].strip().replace(',','')

    # if the channel has the isExplicit class (I believe this global label
    # is applied if any of podcasts are marked as 'E')
    f['isExplicit'] = int(bool(soup.find_all('h1', {'class': 'isExplicit'})))

    # subscriber count
    f['sub_count'] = int(soup.find(class_='sub_count').text.split(':')[-1].strip().replace(',',''))

    # total channel plays for all episodes
    f['play_count'] = int(soup.find(class_='play_count').text.split(':')[-1].strip().replace(',',''))

    # all listed social feeds, including channel website
    f['ch_feed-socials'] = [a.get('href') for a in soup.find(class_='ch_feed-socials').find_all('a')]

    print('episode total div: \n', soup.find(class_='trackListCon_title').text.split('\xa0')[0])
    
    # episode count
    f['ep_total'] = int(soup.find(class_='trackListCon_title').text.split('\xa0')[0].strip().replace(',',''))

    # grab all (visible) episode rows
    visible_eps = soup.find_all(class_='ep-item')
    recent_eps = []

    # iterate through all visible episodes and grab basic info
    for ep in visible_eps:
        ep_name = ep.find('span', class_='ellipsis').text
        ep_date = ep.find('span', class_='date').text
        ep_len = ep.find('span', class_='time').text
        favs = ep.find_all(class_='heart')
#         print(favs[0].parent)
        if len(favs) > 0:
            ep_favs = int(favs[0].parent.text)
        else:
            ep_favs = 0
        recent_eps += [[ep_date, ep_len, ep_favs]]

    f['recent_eps'] = recent_eps

    #### TEXT BASED FEATURES ####

    # grab all of the hover text for all episodes: ep-item-desmodal-con
    f['hover_text_concat'] = ' | '.join([s.text for s in soup.find_all(class_='ep-item-desmodal-con')])

    # channel description
    f['chan_desc'] = soup.find(class_='des-con').text


    f['cover_img_url'] = soup.find(class_='coverImgContainer').find('img').get('src')

    return f


def scrape_channel_page(chan_url, dr, window_rect=(0,0,500,800)):
    '''

    Scrape a single channel page.

    Return a dictionary of features.

    '''
    with open('../logs/scrape_log.txt', 'a') as log:
    
        # append header to logs
        log.write('\n')
        log.write('Now scraping ' + str(chan_url)+ '\n')

        dr.set_window_rect(*window_rect)
        # driver = webdriver.Chrome(chromedriver)

        dr.get(chan_url + '?country=us')

        try:
            # close annoying cookie verification
            cookie = dr.find_element_by_class_name('allow')
            cookie.click()
            log.write(str(dt.datetime.now()) + ' - closed popup')
        except:
            # sometimes the cookie doesn't appear
            pass

        html = dr.page_source
#         print('html:\n', html)
        print(html[-100:])
        assert len(html) != 0

        features = process_channel_soup(chan_url, html)
        log.write(str(dt.datetime.now()) + ' - processed features on page')
        
        time.sleep(5)
        reverse_btn = dr.find_element_by_class_name('funcBtn-item')
        reverse_btn.click()
        log.write(str(dt.datetime.now()) + ' - clicked reverse button' + '\n')
        
        time.sleep(5)

    #     date_path = '/html/body/div/div/div[1]/div/div[2]/div[4]/div[3]/div/div/div/div[1]/div[2]/div/section[1]/div[1]/div[2]/p/span[1]'

    #     date_span = driver.find_element_by_xpath(date_path)
    #     first_pod = date_span.text


        first_pod = dr.find_element_by_class_name('date').text

        features['first_release'] = first_pod
        log.write(str(dt.datetime.now()) + ' - found first date' + '\n')

    #     driver.quit()
        
        return features

#####

def scrape_all_pods_in_category(chan_dict, category, dr, export=False):
    '''
    
    Given a category name, scrape all podcasts in that category.
    
    '''
    
    
    output = ''
    
    category_list = list(chan_dict[category].keys())
    
    # get a list of already scraped channels, to avoid repetition:
    with open('../scraped/channel/already_scraped.csv', 'r') as file:
        scraped = pd.read_csv(file, names=['chan_title','chan_url','category'])
        file.close()
        print('scraped so far:')
        print(' | '.join(list(scraped.chan_title)))
        
    for chan in category_list[:30]:
#         print(chan)
#         print(type(chan))
#         print(len(scraped[scraped.chan_title == chan]))
        if len(scraped[scraped.chan_title == chan]) != 0:
            print('[ skipping: ', chan, ' ] ')
            continue
        
        chan_url = chan_dict[category][chan]['chan_url']
        features = scrape_channel_page(chan_url, dr, window_rect=(0, 0, 600, 1200)) 
        chan_title = features['title']
        
        # add feature dictionary as single line in .txt
        if export==True:
            export_path = '../scraped/channel/by_category/' + category + '.txt'
            with open(export_path, 'a') as file:
                
                feat_dict = {chan_title: features}
                file.write(str(feat_dict) + '\n\n')
                file.close()
            
            # log when channel has been scraped
            export_path = '../scraped/channel/already_scraped.csv'
            with open(export_path, 'a') as file:
                scraped_chan = str(chan) + ',' + str(chan_url) + ',' + str(category)
                file.write(scraped_chan + '\n')
                file.close()
    print('no more channels to scrape')
    dr.quit()
            

def log_test():
    with open('../logs/scrape_log.txt', 'a') as log:
    
        # append header to logs
        log.write('\n')
        log.write(str(dt.datetime.now()))
        log.write('I want this to print')
    log.close()