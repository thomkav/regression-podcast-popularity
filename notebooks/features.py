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
    
#     print(type(recent_eps))
    ep_list = [convert_ep_date(ep[0]) for ep in recent_eps]
#     print(ep_list)
    
    days_bt_eps = []
    for i in range(len(ep_list)-1):
        days_bt_eps += [(abs(ep_list[i+1] - ep_list[i])).days]

    return pd.Series(days_bt_eps).mean()


def lifetime_ep_freq(row):
    '''
    
    approx. episodes / day
    
    =  [ep count] / [age of podcast (up to last activity) in days]
    
    Example:
    df['lifetime_ep_freq'] = df.apply(lifetime_ep_freq, axis=1)
    
    '''
    
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


def avg_ep_len(recent_eps):
    '''
    
    Creates a feature measuring average length of recent ~10 episodes.
    
    Example:
    df['avg_ep_len'] = df.recent_eps.apply(avg_ep_len) 

    
    '''
    
    
    ep_lens = [time.strptime(ep[1], '%H:%M:%S') for ep in recent_eps]
    
#     print(ep_lens)
    avg_ep_len = np.mean(ep_lens)

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


def build_features(df):
    '''
    
    Build feature columns.
    
    '''
    
    
    df['recent_ep_spacing'] = df.recent_eps.apply(ft.recent_ep_mean_dist)
    df['lifetime_ep_freq'] = df.apply(ft.lifetime_ep_freq, axis=1)
    df['avg_ep_len'] = df.recent_eps.apply(ft.avg_ep_len)
    
    social_domains = ['twitter', 'facebook', 'youtube', 'instagram']
    for domain in social_domains:
        df[domain] = df['ch_feed-socials'].apply(ft.has_domain,social_domain=domain)
    
    return df
