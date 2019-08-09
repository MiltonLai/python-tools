#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import time
import pymongo
import config
import newsm_common
import newsm_board
import newsm_article
import newsm_user

now = int(time.time())
print('[*] Setup session')

doc_config = config.tb_config.find_one({'_id': 'login_user'})
if (doc_config is None):
    print('    Failed to read config for login_user. Initiate it.')
    doc_config = {}
    doc_config['_id'] = 'login_user'
    doc_config['val'] = 'guest'
    config.tb_config.save(doc_config)
login_user = doc_config['val']

doc_config = config.tb_config.find_one({'_id': 'login_pass'})
if (doc_config is None):
    print('    Failed to read config for login_pass. Initiate it.')
    doc_config = {}
    doc_config['_id'] = 'login_pass'
    doc_config['val'] = 'guest'
    config.tb_config.save(doc_config)
login_pass = doc_config['val']

newsm_common.login(login_user, login_pass)

print('[*] Update boards')
doc_config = config.tb_config.find_one({'_id': 'boards_updated'})
if (doc_config is None):
    print('    Failed to read config for boards_updated. Initiate it.')
    doc_config = {}
    doc_config['_id'] = 'boards_updated'
    doc_config['at'] = int(time.time()) - 3600 * 24
    config.tb_config.replace_one(doc_config)

time_elapsed = now - doc_config['at']
if (time_elapsed < config.cfg['newsm']['boards_interval']):
    print('    Skip boards updating. Last update elapsed:{}'.format(time_elapsed))
else:
    print('    Proceed boards updating. Last update elapsed:{}'.format(time_elapsed))
    newsm_board.fetch_and_update_boards()
    doc_config['at'] = now
    config.tb_config.replace_one(doc_config)


print('[*] Update articles')
results = config.tb_board.find({}, no_cursor_timeout = True)
selected_boards = []
for board in results:
    time_elapsed = now - board['updated_at']
    #print('{} {}'.format(board, time_elapsed))
    if (board['t1'] == 0 and time_elapsed < 3600 * 4):
        continue
    if (board['t2'] == 0 and time_elapsed < 3600 * 16):
        continue
    if (board['t3'] == 0 and time_elapsed < 3600 * 128):
        continue
    selected_boards.append(board)

print('    Proceed articles updating. Total boards:{}'.format(len(selected_boards)))
for board in selected_boards:
    newsm_article.fetch_new_articles(board)
    newsm_board.update_post_counts(board['_id'])


print('[*] Update users')
# db.getCollection('user').find({next_update :{'$lt': 1563696245}}).sort({next_update:1}).limit(20)
results = config.tb_user.find({'next_update':{'$lt':now}}).sort([('next_update', pymongo.ASCENDING)]).limit(5000)
selected_users = []
for user in results:
    selected_users.append(user)

print('    Proceed users updating. Total users:{}'.format(len(selected_users)))
for user in selected_users:
    newsm_user.update_user(user['name'])

print('[*] Close session')
newsm_common.logout()

print('Done')
