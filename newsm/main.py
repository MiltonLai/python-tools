#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import sys, time
import pymongo
import config, newsm_common, newsm_article, newsm_board, newsm_user
from config import logger

if len(sys.argv) > 2:
    global_mode = 1
    single_board_id = int(sys.argv[1])
    single_board_start_page = int(sys.argv[2])
    if single_board_id <= 0:
        logger.info('Error: Invalid board ID: {}'.format(single_board_id))
    else:
        logger.info('[*] Mode: Single, Board: {}, From Page: {}'.format(single_board_id, single_board_start_page))
else:
    global_mode = 0
    logger.info('[*] Mode: All')

now = int(time.time())
logger.info('[*] Setup session')

doc_config = config.tb_config.find_one({'_id': 'login_user'})
if (doc_config is None):
    logger.info('    Failed to read login confidential. Now initiate it.')
    doc_config = {}
    doc_config['_id'] = 'login_user'
    doc_config['val'] = 'guest'
    config.tb_config.save(doc_config)
login_user = doc_config['val']

doc_config = config.tb_config.find_one({'_id': 'login_pass'})
if (doc_config is None):
    logger.info('    Failed to read config for login_pass. Initiate it.')
    doc_config = {}
    doc_config['_id'] = 'login_pass'
    doc_config['val'] = 'guest'
    config.tb_config.save(doc_config)
login_pass = doc_config['val']

newsm_common.login(login_user, login_pass)

logger.info('[*] Update boards')
doc_config = config.tb_config.find_one({'_id': 'boards_updated'})
if (doc_config is None):
    logger.info('    Failed to read config for boards_updated. Initiate it.')
    doc_config = {}
    doc_config['_id'] = 'boards_updated'
    doc_config['at'] = int(time.time()) - 3600 * 24
    config.tb_config.save(doc_config)

time_elapsed = now - doc_config['at']
if (time_elapsed < config.cfg['newsm']['boards_interval']):
    logger.info('    Skip boards updating. Last update elapsed:{}'.format(time_elapsed))
else:
    logger.info('    Proceed boards updating. Last update elapsed:{}'.format(time_elapsed))
    newsm_board.fetch_and_update_boards()
    doc_config['at'] = now
    config.tb_config.save(doc_config)

logger.info('[*] Update articles')
if global_mode == 0:
    results = config.tb_board.find({}, no_cursor_timeout=True)
    selected_boards = []
    for board in results:
        time_elapsed = now - board['updated_at']
        # print('{} {}'.format(board, time_elapsed))
        if (board['t3'] == 0 and time_elapsed < 3600 * 128):
            continue
        if (board['t2'] == 0 and time_elapsed < 3600 * 16):
            continue
        # t1[160,) always; t1[80,160) every 30 min; t1[20,80) every 1 hour; t1[0,20) every 4 hours
        if (board['t1'] < 20 and time_elapsed < 3600 * 4):
            continue
        if (board['t1'] < 80 and time_elapsed < 3600):
            continue
        if (board['t1'] < 160 and time_elapsed < 1800):
            continue

        selected_boards.append(board)
    logger.info('    Proceed articles updating. Total boards:{}'.format(len(selected_boards)))
    for board in selected_boards:
        newsm_article.fetch_new_articles(board)
        newsm_board.update_post_counts(board['_id'])
else:
    board = config.tb_board.find_one({'_id': single_board_id})
    if board is None:
        logger.info('    Board not found:{}'.format(single_board_id))
    else:
        logger.info('    Proceed articles updating for board:{}'.format(single_board_id))
        newsm_article.fetch_new_articles(board, single_board_start_page)
        newsm_board.update_post_counts(board['_id'])

logger.info('[*] Update users')
if global_mode == 0:
    # db.getCollection('user').find({next_update :{'$lt': 1563696245}}).sort({next_update:1}).limit(20)
    results = config.tb_user.find({'next_update': {'$lt': now}}).sort([('next_update', pymongo.ASCENDING)]).limit(300)
    selected_users = []
    for user in results:
        selected_users.append(user)

    logger.info('    Proceed users updating. Total users:{}'.format(len(selected_users)))
    for user in selected_users:
        newsm_user.update_user(user['name'])
else:
    logger.info('    Skipped in Single mode')

logger.info('[*] Close session')
newsm_common.logout()

logger.info('Done')
