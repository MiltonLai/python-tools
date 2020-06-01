#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import re
import time

import config, newsm_common


def update_post_counts(board_id):
    board = config.tb_board.find_one({'_id': board_id})
    if (board is None):
        print('Board is null: {}'.format(board_id))
        exit()
    now = int(time.time())
    if (('article_' + str(board_id)) in config.mongo_db.collection_names()):
        tb_article = config.mongo_db['article_' + str(board_id)]
        board['t1'] = tb_article.count_documents({'created_at': {'$gt': now - 3600 * 4}})
        board['t2'] = tb_article.count_documents({'created_at': {'$gt': now - 3600 * 16}})
        board['t3'] = tb_article.count_documents({'created_at': {'$gt': now - 3600 * 128}})
        board['post_count'] = tb_article.estimated_document_count()
    else:
        board['t1'] = 0
        board['t2'] = 0
        board['t3'] = 0
        board['post_count'] = 0
    board['updated_at'] = now
    config.tb_board.save(board)

def fetch_and_update_boards():
    all_boards = browseSection(0)
    print('Finished fetching all boards. Total:{}. May contain duplicate ids.'.format(len(all_boards)))
    flag_new = False
    flag_update = False
    for board in all_boards:
        del board['section_id']
        del board['parent_id']
        dummy = config.tb_board.find_one({'_id': board['_id']})
        if (dummy is None):
            flag_new = True
            # if board doesn't exist, save the new row
            board['t1'] = 1
            board['t2'] = 1
            board['t3'] = 1
            board['updated_at'] = int(time.time())
            config.tb_board.save(board)
            print('New board found and saved. Board:{}, {}, {}'.format(board['_id'], board['name'], board['name2']))
        elif (dummy['name'] != board['name']):
            flag_update = True
            old_name = dummy['name']
            dummy['name'] = board['name']
            config.tb_board.save(dummy)
            print('Board name updated. Board:{}, {}, old name:{}'.format(board['_id'], board['name'], old_name))

    if (not flag_new):
        print('No new boards found.')
    if (not flag_update):
        print('No board updates found.')


def browseSection(id):
    url = config.base_url + '/bbsfav.php?select=' + str(id) + '&x'
    content = newsm_common.request_get(url, 'GB18030', 20, 10)
    content = content.replace(u'\u3000', u'')
    #print(content)
    boards = []
    # list all sections
    result = re.compile(r'o\.f\([^\)]*\)').findall(content)
    if (len(result) > 0):
        for line in result:
            match = re.match(r'o\.f\((\d+),\'([^\s]*)\s+(.*)\',(\d+),\'(.*)\'\)', line)
            section = {}
            section['parent_id'] = id
            section['_id'] = int(match.group(1))
            section['name'] = match.group(5)
            section['name2'] = match.group(2)
            section['desc'] = match.group(3)
            section['rank'] = int(match.group(4))
            #all_sections.append(section)
            #print(section)
            sub_boards = browseSection(section['_id'])
            boards.extend(sub_boards)

    # list all boards
    # o.o(false,1,1161,23473,'[清华]','CECM.THU','清华土木建管','ghostzb',21767,0,1);
    # 版面or目录, group, group2, (不知道), 分区名, 版面名, 版面中文名, 版主(可能为空), 帖子数, (不知道), 在线数
    result = re.compile(r'o\.o\([^\)]*\)').findall(content)
    #print(result)
    for line in result:
        match = re.match(r'o\.o\((true|false),(\d+),(\d+),(\d+),\'\[([^\]]*)\]\',\s*\'([^\']+)\',\s*\'([^\']+)\',\s*\'([^\']*)\',(\d+),(\d+),(\d+)\)', line)
        #print(match.group())
        board = {}
        board['_id'] = int(match.group(3))
        board['name'] = match.group(6)
        board['name2'] = match.group(7)
        board['moderators'] = match.group(8)
        board['section_name'] = match.group(5)
        board['unkown1'] = int(match.group(4))
        board['unkown2'] = int(match.group(10))
        board['online'] = int(match.group(11))
        board['is_folder'] = match.group(1)
        board['post_count'] = int(match.group(9))
        board['section_id'] = id
        board['parent_id'] = 0
        boards.append(board)
        # print(board)
        if board['is_folder'] == 'true':
            sub_boards = browseBoard(board['name'], board['_id'], id)
            boards.extend(sub_boards)
    return boards


def browseBoard(name, id, sectionId):
    url = config.base_url + '/bbsdoc.php?board=' + name
    content = newsm_common.request_get(url, 'GB18030', 20, 10)
    content = content.replace(u'\u3000', u'')
    #print(content)
    boards = []
    result = re.compile(r'o\.o\([^\)]*\)').findall(content)
    #print(result)
    for line in result:
        match = re.match(
            r'o\.o\((true|false),(\d+),(\d+),(\d+),\'\[([^\]]*)\]\',\s*\'([^\']+)\',\s*\'([^\']+)\',\s*\'([^\']*)\',(\d+),(\d+),(\d+)\)',
            line)
        # print(match.group())
        board = {}
        board['_id'] = int(match.group(3))
        board['name'] = match.group(6)
        board['name2'] = match.group(7)
        board['moderators'] = match.group(8)
        board['section_name'] = match.group(5)
        board['unkown1'] = int(match.group(4))
        board['unkown2'] = int(match.group(10))
        board['online'] = int(match.group(11))
        board['is_folder'] = match.group(1)
        board['post_count'] = int(match.group(9))
        board['section_id'] = sectionId
        board['parent_id'] = id
        boards.append(board)
        # print(board)
        if board['is_folder'] == 'true':
            sub_boards = browseBoard(board['name'], board['_id'], sectionId)
            boards.extend(sub_boards)
    return boards
