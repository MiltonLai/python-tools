#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import pymongo
import re
import time

import config, newsm_common
from config import logger


def update_user(name):
    if name == 'deliver':
        return

    dummy = config.tb_user.find_one({'_id': name.lower()})
    if dummy is None:
        user = fetch_user(name)
        if not user is None:
            logger.info('    New:      {}, {}, {}, {}'.format(user['name'], user['nick'], str(user['logins']), str(user['posts'])))
            config.tb_user.save(user)
    else:
        # if user has been updated within 24 hours, skip
        if int(time.time()) - dummy['updated_at'] < 3600 * 24:
            # print('Skip {}'.format(name))
            return
        else:
            user = fetch_user(name)
            if user is not None:
                flag_changed = False
                if user['nick'] == '用户不存在':
                    # skip all Non-exists users
                    flag_changed = False
                else:
                    # fetch the latest snapshot
                    snapshots = config.tb_user_snapshot.find({'_id': {'$regex': '^' + name.lower() + '\.\d+'}}).sort([('_id', pymongo.DESCENDING)]).limit(5)
                    if snapshots.count() == 0:
                        # Save a snapshot if there is none
                        flag_changed = True
                    else:
                        # Compare with the latest snapshot
                        snapshot = snapshots[0]
                        if compare_snapshot(snapshot, user) or compare_user(dummy, user):
                            flag_changed = True

                if flag_changed:
                    dummy['_id'] = dummy['_id'] + '.' + str(dummy['updated_at'])
                    del dummy['next_update']
                    config.tb_user_snapshot.save(dummy)
                    config.tb_user.save(user)
                    logger.info('    Changed:  {}, {}, {}, {}'.format(user['name'], user['nick'], str(user['logins']), str(user['posts'])))
                else:
                    config.tb_user.save(user)
                    logger.info('    Unchanged:{}, {}, {}, {}'.format(user['name'], user['nick'], str(user['logins']), str(user['posts'])))
            else:
                logger.info("None user")


def compare_user(old_user, new_user):
    if old_user['name'] != new_user['name']:
        return True
    if old_user['nick'] != new_user['nick']:
        return True
    if new_user['posts'] - old_user['posts'] > 20:
        return True
    if old_user['ip'] != new_user['ip']:
        return True

    return False


def compare_snapshot(snapshot, new_user):
    if new_user['logins'] - snapshot['logins'] > 50:
        return True
    if new_user['posts'] - snapshot['posts'] > 20:
        return True

    return False


def fetch_user(name):
    url = config.base_url + '/bbsqry.php?userid=' + name
    html = newsm_common.request_get(url, 'GB18030', 20, 10)
    # logger.info(html)
    if html is None:
        logger.error('URL request failed: ' + url)
        return None
    '''<tr><td>该用户不存在</td></tr>'''
    result = re.compile('<tr><td>该用户不存在</td></tr>').search(html)
    if result is not None:
        user = {
            '_id': name.lower(),
            'name': name,
            'nick': '用户不存在',
            'logins': 0,
            'posts': 0,
            'last_login': '',
            'ip': '',
            'last_active': '',
            'life': 0,
            'title': '',
            'updated_at': int(time.time()),
            'next_update': int(time.time()) + 3600 * 240
        }
        return user

    result = re.compile('<pre>\s*([\s\S]*)\s*</pre>').search(html)
    if result is None:
        logger.error('    Not matched: {}'.format(html))
        return None
    # logger.info(result.group(1))
    result2 = re.compile('([^(]+)\(([\s\S]*)\) 共上站 (\d+) 次，发表过 (\d+) 篇文章\s+上次在\s+\[(.*)\] 从 \[(.*)\] 到本站一游。(?:积分: \[\d+\])?\s+离线时间\s*\[(.*)\] 信箱: \[(.*)\] 生命力: \[(-?\d+)\] 身份: \[(.*)\]。').search(result.group(1))
    if result2 is None:
        logger.error('Not matched(2)')
        logger.debug(result.group())
        return None
    # logger.info(result2.group())
    user = {
        '_id': name.lower(),
        'name': result2.group(1).strip(),
        'nick': result2.group(2).strip(),
        'logins': int(result2.group(3)),
        'posts': int(result2.group(4)),
        'last_login': result2.group(5),
        'ip': result2.group(6),
        'last_active': result2.group(7),
        'life': int(result2.group(9)),
        'title': result2.group(10),
        'updated_at': int(time.time()),
        'next_update': int(time.time()) + 3600 * 72
    }

    result3 = re.compile('\'dp1\'\);\s+prints\(\'(.*)\'\);\/\/-->').search(html)
    # logger.debug(result3.group())
    if result3 is not None:
        user['signature'] = result3.group(1).strip()
        user['signature'] = re.sub(r'\\n', '\n', user['signature'])
        user['signature'] = re.sub(r'\\r\[[;\d]{0,12}m', '', user['signature'])
        user['signature'] = re.sub(r'\\(/|"|\')', r'\1', user['signature'])
        user['signature'] = user['signature'].strip()
    else:
        user['signature'] = None

    return user
