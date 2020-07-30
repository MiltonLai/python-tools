#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import os
import pymongo
import yaml
import logging
from logging import handlers

# The path of current file(config.py, not the file that includes it). can test with os.path.realpath(__file__)
rootPath = os.path.dirname(__file__)
configPath = os.path.join(rootPath,'config.yml')

with open(configPath, 'r') as ymlfile:
    cfg = yaml.safe_load(ymlfile)

# setup logger
if not 'logger' in cfg:
    exit(1)

logger = logging.getLogger(__name__)
if 'mode' in cfg['logger']:
    if cfg['logger']['mode'] == 'file':
        handler = handlers.TimedRotatingFileHandler(
            filename=cfg['logger']['filepath'],
            when=cfg['logger']['when'],
            backupCount=cfg['logger']['backcount'],
            encoding='utf-8')
    else:
        handler = logging.StreamHandler()
else:
    handler = logging.StreamHandler()
logger.addHandler(handler)

if 'level' in cfg['logger']:
    logger.setLevel(cfg['logger']['level'])
    handler.setLevel(cfg['logger']['level'])

if 'formatter' in cfg['logger']:
    formatter = logging.Formatter(cfg['logger']['formatter'], '%m%d %H%M%S')
else:
    formatter = logging.Formatter('%(asctime)s %(pathname)s[%(lineno)d] %(levelname).1s: %(message)s')
handler.setFormatter(formatter)

# mongodb connection
mongoclient = pymongo.MongoClient(cfg['mongo']['host'], cfg['mongo']['port'])
mongo_db = mongoclient[cfg['mongo']['db']]
if 'user' in cfg['mongo']:
    logger.info("Auth checking with user " + cfg['mongo']['user'])
    mongo_db.authenticate(cfg['mongo']['user'], cfg['mongo']['pwd'], mechanism=cfg['mongo']['mechanism'])

tb_config = mongo_db['config']
tb_section = mongo_db['section']
tb_board = mongo_db['board']
tb_section_to_board = mongo_db['section_to_board']
tb_user = mongo_db['user']
tb_user_snapshot = mongo_db['user_snapshot']

base_url = cfg['newsm']['base_url']
if ('proxies' in cfg):
    logger.info("Proxy is ON")
    proxies = cfg['proxies']
else:
    logger.info("Proxy is OFF")
    proxies = None