#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import re
import time
import pymongo

import config, newsm_common

now = int(time.time())

mongoclient = pymongo.MongoClient('127.0.0.1', 27017)
mongo_db2 = mongoclient['smth']
src_board = mongo_db2['board']
src_user = mongo_db2['user']


print('[*] Import boards')
results = src_board.find({})
all_boards = []
for result in results:
    board = {}
    board['_id']            = result['_id']
    board['name']           = result['name']
    board['name2']          = result['name2']
    board['moderators']     = result['moderators']
    board['section_name']   = result['section_name']
    board['unkown1']        = result['unkown1']
    board['unkown2']        = result['unkown2']
    board['online']         = result['online']
    board['is_folder']      = result['is_folder']
    board['post_count']     = result['post_count']
    board['t1'] = 1
    board['t2'] = 1
    board['t3'] = 1
    board['updated_at']     = result['updatedAt']
    config.tb_board.save(board)
    all_boards.append(board)

'''
print('[*] Import users')
total = src_user.estimated_document_count()
results = src_user.find({})
count = 0
for result in results:
    user = {}
    user['_id']         = result['_id'].lower()
    user['name']        = result['_id']
    user['nick']        = result['nick']
    user['logins']      = result['logins']
    user['posts']       = result['posts']
    user['last_login']  = result['lastLogin']
    user['ip']          = result['ip']
    user['last_active'] = result['lastActive']
    user['life']        = result['life']
    user['title']       = result['title']
    user['updated_at']  = result['updatedAt']
    user['next_update'] = result['updatedAt']
    if ('signature' in result):
        user['signature'] = re.sub(r'\\n', '\n', result['signature'])
        user['signature'] = re.sub(r'\\r\[[;\d]{0,12}m', '', user['signature'])
        user['signature'] = re.sub(r'\\(/|"|\')', r'\1', user['signature'])
        user['signature'] = user['signature'].strip()
    else:
        user['signature'] = None

    config.tb_user.save(user)
    count += 1
    if (count % 1000 == 0):
        print('{} / {}'.format(count, total))
'''

print('[*] Import articles')
board_skip = 995
board_count = 0
for board in all_boards:
    if (board['_id'] < board_skip):
        continue

    tb_article = config.mongo_db['article_' + str(board['_id'])]
    src_article = mongo_db2['article_' + str(board['_id'])]
    total = src_article.estimated_document_count()
    results = src_article.find({})
    board_count += 1
    count = 0
    articles = []
    for result in results:
        article = {}
        article['_id'] = result['_id']
        article['title'] = newsm_common.remove_emoji(result['title'].strip())
        article['parent_id'] = result['parentId']
        article['author'] = result['author'].strip()
        article['size'] = result['size']
        article['flag'] = result['flag'].strip()
        article['board_name'] = result['boardName'].strip()
        article['board_id'] = result['boardId']
        # simplifiy the content
        if ('content' in result):
            article['content'] = re.sub(r'\\n', '\n', result['content'])
            article['content'] = re.sub(r'\\r\[[;\d]{0,8}m', '', article['content'])
            article['content'] = re.sub(r'\\(/|"|\')', r'\1', article['content'])
            article['content'] = newsm_common.remove_emoji(article['content'])
        else:
            article['content'] = ''

        article['ip'] = None if (not 'ip' in result) else result['ip']
        article['created_at'] = result['createdAt']
        article['updated_at'] = result['createdAt'] if (not 'updatedAt' in result) else result['updatedAt']
        article['attachments'] = None if (not 'attachments' in result) else result['attachments']
        articles.append(article)
        count += 1
        if (count % 20000 == 0):
            tb_article.insert_many(articles)
            articles = []
            print('{} {}: {} / {}'.format(board_count, board['_id'], count, total))

    if (len(articles) > 0):
        tb_article.insert_many(articles)

print('Done')
