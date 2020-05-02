#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import time
import pymongo

from newsm import config

now = int(time.time())

print('[*] List all collections')
results = config.mongo_db.collection_names()
selected_boards = []
for result in results:
    if (result.startswith('article')):
        selected_boards.append(result)
    else:
        print('Skip:{}'.format(result))

print('Total:{}'.format(len(selected_boards)))
count = 0
for board in selected_boards:
    count += 1
    board_col = config.mongo_db[board]
    indexes = board_col.list_indexes()
    flag_author = True
    flag_created_at = True
    for index in indexes:
        #print(index)
        #print(index['name'])
        if (index['name'] == 'author_text_created_at_-1'):
            board_col.drop_index('author_text_created_at_-1')
        if (index['name'] == 'author_text'):
            flag_author = False
        if (index['name'] == 'created_at_-1'):
            flag_created_at = False
    if (flag_author):
        print('Add author index:{}'.format(board))
        board_col.create_index([('author', pymongo.TEXT)])
    if (flag_created_at):
        print('Add created_at index:{}'.format(board))
        board_col.create_index([('created_at', pymongo.DESCENDING)])

print('Done')
