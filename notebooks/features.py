# Pre-processing pipeline for raw, scraped podcast records.
# Sanitizes category dataframes.
# Creates feature columns.

import pickle
import random
import sys, os
from datetime import datetime
import pandas as pd
import math
import time
import re
import numpy as np
import ast
import tldextract



def convert_ep_date(string):
    '''
    
    Conversion for date format found in podcast scrapes.
    
    '''
    
    return datetime.strptime(string, '%Y-%m-%d')


def recent_ep_mean_dist(recent_eps):
    '''
    
    Takes the raw `recent_eps` column as input series.
    Returns the mean time delta between episodes.
    
    Example:
    df['recent_ep_spacing'] =
        df.recent_eps.apply(recent_ep_mean_dist)
    
    
    '''
    
    try:
    #     print(type(recent_eps))
        ep_list = [convert_ep_date(ep[0]) for ep in recent_eps]
    #     print(ep_list)

        days_bt_eps = []
        for i in range(len(ep_list)-1):
            days_bt_eps += [(abs(ep_list[i+1] - ep_list[i])).days]

        return pd.Series(days_bt_eps).mean()
    
    except:
        return 914.3 # mean age


def lifetime_ep_freq(row):
    '''
    
    approx. episodes / day
    
    =  [ep count] / [age of podcast (up to last activity) in days]
    
    Example:
    df['lifetime_ep_freq'] = df.apply(lifetime_ep_freq, axis=1)
    
    '''
    try:
        last_ep_date = convert_ep_date(row['recent_eps'][0][0])
        release_date = convert_ep_date(row['first_release'])
        ep_total = row['ep_total']



        age = (last_ep_date - release_date).total_seconds() / (24. * 60. * 60.)

        if age == 0:
            freq = 0
        else:
            freq = ep_total / age

        #     print(last_ep_date, release_date, ep_total, age, freq)


        return freq
    
    except:
        return 0

def chan_age(row):
    '''
    
    time b/t first and latest podcast
    
    Example:
    df['lifetime_ep_freq'] = df.apply(chan_age, axis=1)
    
    '''
    try:
        last_ep_date = convert_ep_date(row['recent_eps'][0][0])
        release_date = convert_ep_date(row['first_release'])
        ep_total = row['ep_total']



        age = (last_ep_date - release_date).total_seconds() / (24. * 60. * 60.)

        if type(age) == float:
            return age
        else:
            return 0
    except:
        return 0


def avg_ep_len(recent_eps):
    '''
    
    Creates a feature measuring average length of recent ~10 episodes.
    
    Example:
    df['avg_ep_len'] = df.recent_eps.apply(avg_ep_len) 

    
    '''
    
    
    try:
        ep_lens = []
        for ep in recent_eps:
            try:
                parsed_time = time.strptime(ep[1], '%H:%M:%S')
                ep_lens += [parsed_time]
            except:
                pass
    except:
        print(f'time parse error with entry {recent_eps}')
        return 0
    
#     print(ep_lens)
    try:
        avg_ep_len = np.mean(ep_lens)
    except:
        return 0

    return avg_ep_len


def has_domain(row, social_domain):
    '''
    
    Create binary classifier regarding the existence of various social feeds.
    
    Usage:
    
    social_domains = ['twitter', 'facebook', 'youtube', 'instagram']
    
    for domain in social_domains:
        df[domain] = df['ch_feed-socials'].apply(has_domain,social_domain=domain)
    
    
    '''
    
    
    ch_feed_socials = row
    for link in ch_feed_socials:
        pattern = '.*' + social_domain + '.*'
#         print(pattern, link)
#         print(re.match(pattern, link))
        if re.match(pattern, link):
            return 1
    return 0


def try_casting_to_int(ep_total):
    '''
    
    Corrects for an early scraping error when I wasn't properly casting ep_total to an int.
    
    '''
    
    if type(ep_total) != int:
        try:
            return int(ep_total)
        except:
            return 0
    else:
        return ep_total


def sanitize(df):
    '''
    
    General sanitization as I find errors with various datasets.
    
    '''
    
    
    
    df['ep_total'] = df.ep_total.apply(try_casting_to_int)
    
    # I accidentally grabbed duplicate content in initial scrapes.
    try:
        df.drop(columns='description', inplace=True)
    except:
        pass
    
    return df

def raw_to_df(cat_name):
    
    cat_dict = {}
    
    filename = '../scraped/channel/by_category/' + cat_name + '.txt'
    
    with open(filename, 'r') as file:
        
        for line in file:
            
            try:
                pod_dict = ast.literal_eval(line)
                chan_name = [k for k in pod_dict.keys()][0]
                cat_dict[chan_name] = pod_dict[chan_name]
            except:
                continue
        
    df = pd.DataFrame.from_dict(cat_dict, orient='index')
    df = df.reset_index().drop(labels='index',axis=1)
    df['category'] = cat_name 
    
    # various sanitation tasks
    df = sanitize(df)

    export_path = '../scraped/channel/by_category/' + cat_name + '.pickle'
    with open(export_path, 'wb') as file:
        pickle.dump(df, file)
    
    return df


def merge_raw_data(scraped_categories):
    '''
    
    Take a list of scraped categories in its directory,
    and append 
    
    '''
    
    # append other dataframes to base dataframe
    for scraped in scraped_categories:
        
        next_df = ft.raw_to_df(scraped)
        print(f'loaded {scraped} with size {next_df.shape}')
        
        try:
            print('appending... ', scraped)
            df = df.append(next_df)
        except:
            print('first dataframe... ', scraped)
            df = next_df.copy()
        
        print(f'dataframe now has size {df.shape}')
        
        
    return df

def get_twitter_follower_count(title):
    '''
    
    Pull the follower count for a podcast,
    if it exists in a dictionary of channels.
    
    If it doesn't exist, return 0.
    
    
    '''
    
    
    with open('../social_metrics/twitter/channel_stats_by_name_oct8_2p.pickle', 'rb') as file:
        twitter_dict = pickle.load(file)
        
    try:
        return twitter_dict[title]['follower_count']
    except:
        return 0
    
social_domains = ['twitter', 'facebook', 'youtube', 'instagram']
with open('../social_metrics/external_domains/external_domain_dicts.pickle','rb') as file:
    domain_dict = pickle.load(file)

def return_external_site_domain(ch_feed_socials):
    '''
    
    Return a non-social external domain from a list of domains.abs
    
    If one does not exist, return False
    
    
    '''
    
#     print(ch_feed_socials)
    
    if not ch_feed_socials:
        return False
    
    for link in ch_feed_socials:
        external = link
#         print('testing ', link)
        social_domains = ['twitter', 'facebook', 'youtube', 'instagram']
        for domain in social_domains:
            pattern = '.*' + domain + '.*'
    #         print(pattern, link)
    #         print(re.match(pattern, link))
            if re.match(pattern, link):
#                 print('matches ',domain)
                external = ''
                break

    return external

def extract_domain(site):
    try:
        domain_name = tldextract.extract(site).domain + '.' + tldextract.extract(site).suffix
        return domain_name
    except:
        return ''
    

def build_features(df, feature_set='episode'):
    '''
    
    Build all feature columns in one shot.
    
    feature_set: feature sets to develop        
        'episode' (default)
            - recent_ep_spacing
            - lifetime_ep_freq
            - avg_ep_len
            - chan_age
        
        'social'
            - has_twitter
            - has_facebook
            - has_youtube
            - has_twitterchan_age
      
    
    '''


    #################################################
    # Episode Time Series Features
    #################################################
    
    if feature_set=='episode':
        print('building episode time series features')
        try:
            df['recent_ep_spacing'] = df.recent_eps.apply(recent_ep_mean_dist)
        except:
            print('Error: failed to build recent_ep_spacing feature')

        try:
            df['lifetime_ep_freq'] = df.apply(lifetime_ep_freq, axis=1)
        except:
            print('Error: failed to build lifetime_ep_freq feature')

        try:
            df['avg_ep_len'] = df.recent_eps.apply(avg_ep_len)
        except:
            print('Error: failed to build avg_ep_len feature')

        try:
            df['chan_age'] = df.apply(chan_age, axis=1)
        except:
            print('Error: failed to build chan_age feature')
    
    #################################################
    # Social Account Metrics
    #################################################
    
    if feature_set=='social':
        print('building social media features')
        social_domains = ['twitter', 'facebook', 'youtube', 'instagram']
        for domain in social_domains:
            try:
                df['has_'+domain] = df['ch_feed-socials'].apply(has_domain,social_domain=domain)
            except:
                print(f'Error: failed to build has_{domain} binary feature')

        try:
            df['twitter_followers'] = df.title.apply(get_twitter_follower_count)
        except:
            print('Error: failed to build twitter_followers feature')
            
    
    
    return df
