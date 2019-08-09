#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import re
import time

import config
import newsm_common

def update_user(name):
    if (name == 'deliver'):
        return

    dummy = config.tb_user.find_one({'_id': name})
    if (dummy is None):
        user = fetch_user(name)
        if (not user is None):
            config.tb_user.save(user)
    else:
        # if user has been updated within 24 hours, skip
        if (int(time.time()) - dummy['updated_at'] < 3600 * 24):
            #print('Skip {}'.format(name))
            return
        else:
            user = fetch_user(name)
            if (not user is None):
                flag_changed = compare_user(dummy, user)
                if (flag_changed):
                    dummy['_id'] = dummy['_id'] + '.' + str(dummy['updated_at'])
                    del dummy['next_update']
                    config.tb_user_snapshot.save(dummy)
                    config.tb_user.save(user)
                    print('    Changed:  {}, {}, {}, {}'.format(user['name'], user['nick'], str(user['logins']), str(user['posts'])))
                else:
                    config.tb_user.save(user)
                    print('    Unchanged:{}, {}, {}, {}'.format(user['name'], user['nick'], str(user['logins']), str(user['posts'])))
            else:
                print("None user")

def compare_user(old_user, new_user):
    flag_changed = False
    if (old_user['name'] != new_user['name']):
        flag_changed = True
    if (old_user['nick'] != new_user['nick']):
        flag_changed = True
    if (new_user['posts'] - old_user['posts'] > 20):
        flag_changed = True
    if (old_user['ip'] != new_user['ip']):
        flag_changed = True
    return flag_changed

def fetch_user(name):
    url = config.base_url +'/bbsqry.php?userid=' + name
    html = newsm_common.request_get(url, 'GB18030', 20, 10)
    #print(html)
    if html is None:
        print('URL request failed: '+ url)
        return None
    '''<tr><td>该用户不存在</td></tr>'''
    result = re.compile('<tr><td>该用户不存在</td></tr>').search(html)
    if (not result is None):
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
        print('    Not matched: {}'.format(html))
        return None
    # print(result.group(1))
    result2 = re.compile('[^(]+\(([\s\S]*)\) 共上站 (\d+) 次，发表过 (\d+) 篇文章\s+上次在\s+\[(.*)\] 从 \[(.*)\] 到本站一游。(?:积分: \[\d+\])?\s+离线时间\s*\[(.*)\] 信箱: \[(.*)\] 生命力: \[(-?\d+)\] 身份: \[(.*)\]。').search(result.group(1))
    if result2 is None:
        print('Not matched(2)')
        print(result.group())
        return None
    #print(result2.group())
    user = {
        '_id': name.lower(),
        'name': name,
        'nick': result2.group(1).strip(),
        'logins': int(result2.group(2)),
        'posts': int(result2.group(3)),
        'last_login': result2.group(4),
        'ip': result2.group(5),
        'last_active': result2.group(6),
        'life': int(result2.group(8)),
        'title': result2.group(9),
        'updated_at': int(time.time()),
        'next_update': int(time.time()) + 3600 * 72
    }

    result3 = re.compile('\'dp1\'\);\s+prints\(\'(.*)\'\);\/\/-->').search(html)
    #print(result3.group())
    if (not result3 is None):
        user['signature'] = result3.group(1).strip()
        user['signature'] = re.sub(r'\\n', '\n', user['signature'])
        user['signature'] = re.sub(r'\\r\[[;\d]{0,12}m', '', user['signature'])
        user['signature'] = re.sub(r'\\(/|"|\')', r'\1', user['signature'])
        user['signature'] = user['signature'].strip()
    else:
        user['signature'] = None

    return user
