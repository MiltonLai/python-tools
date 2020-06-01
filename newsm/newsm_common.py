#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import re
import requests
import time
import config

session = requests.session()

def login(user_name, user_pass):
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0',
        'Referer': config.base_url + '/indexpages/default/',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    })
    #print(session.headers)
    #print(session.cookies.get_dict())
    #res = session.get(config.base_url + '/frames.php', proxies=config.proxies)

    post_data = {'id':user_name,'passwd': user_pass}
    rs = session.post(config.base_url + '/bbslogin1203.php', post_data, proxies=config.proxies)
    print(session.cookies.get_dict())

def logout():
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0',
        'Referer': config.base_url + '/bbsguestleft.html',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    })
    #print(session.cookies.get_dict())
    res = session.get(config.base_url + '/bbslogout.php', proxies=config.proxies)
    #print(session.cookies.get_dict())

def request_get(url, encoding='UTF-8', tout=20, retries=10):
    count = 0
    while True:
        count += 1
        if (count > retries):
            print('Exceed retry limit')
            return None
        time.sleep(1)
        try:
            response = session.get(url, timeout=tout, proxies=config.proxies)
            response.encoding = encoding
            #print(response.text)
            return response.text
        except requests.ReadTimeout:
            print('ReadTimeout')
            continue
        except ConnectionError:
            print('ConnectionError')
            continue
        except requests.RequestException:
            print('RequestException')
            continue

def remove_emoji(text):
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)  # no emoji
    
    

