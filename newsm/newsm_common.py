#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import re
import requests
import time
import config
from config import logger

session = requests.session()

def login(user_name, user_pass):
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0',
        'Referer': config.base_url + '/nForum/',
        'Accept': 'application/json, text/javascript, */*; q=0.01'
    })
    logger.debug(session.headers)
    logger.debug(session.cookies.get_dict())
    response = session.get(config.base_url + '/nForum/', proxies=config.proxies)
    response.encoding = 'UTF-8'
    logger.debug(session.cookies.get_dict())
    post_data = {'id':user_name,'passwd': user_pass}
    res = session.post(
        config.base_url + '/nForum/user/ajax_login.json',
        post_data,
        headers={'X-Requested-With': 'XMLHttpRequest'},
        proxies=config.proxies)
    logger.info(res.text)
    logger.info(session.cookies.get_dict())

def logout():
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:68.0) Gecko/20100101 Firefox/68.0',
        'Referer': config.base_url + '/nForum/',
        'Accept': 'application/json, text/javascript, */*; q=0.01'
    })
    #logger.info(session.cookies.get_dict())
    res = session.get(
        config.base_url + '/nForum/user/ajax_logout.json',
        headers={'X-Requested-With': 'XMLHttpRequest'},
        proxies=config.proxies)
    #logger.info(session.cookies.get_dict())

def request_get(url, encoding='UTF-8', tout=20, retries=10):
    count = 0
    while True:
        count += 1
        if (count > retries):
            logger.error('Exceed retry limit')
            return None
        time.sleep(0.2)
        try:
            response = session.get(url, timeout=tout, proxies=config.proxies)
            response.encoding = encoding
            #print(response.text)
            return response.text
        except requests.ReadTimeout:
            logger.error('ReadTimeout')
            continue
        except ConnectionError:
            logger.error('ConnectionError')
            continue
        except requests.RequestException:
            logger.error('RequestException')
            continue

def remove_emoji(text):
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(r'', text)  # no emoji
    
    

