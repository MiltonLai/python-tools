#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import os
import pymongo
import yaml


# The path of current file(config.py, not the file that includes it). can test with os.path.realpath(__file__)
rootPath = os.path.dirname(__file__)
configPath = os.path.join(rootPath,'config.yml')

with open(configPath, 'r') as ymlfile:
    cfg = yaml.safe_load(ymlfile)

mongoclient = pymongo.MongoClient(cfg['mongo']['host'], cfg['mongo']['port'])
mongo_db = mongoclient[cfg['mongo']['db']]
tb_config = mongo_db['config']
tb_section = mongo_db['section']
tb_board = mongo_db['board']
tb_section_to_board = mongo_db['section_to_board']
tb_user = mongo_db['user']
tb_user_snapshot = mongo_db['user_snapshot']

base_url = cfg['newsm']['base_url']
