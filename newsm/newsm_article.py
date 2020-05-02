#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import re
import time

from newsm import config, newsm_common, newsm_user


def fetch_new_articles(board):
    url = config.base_url + '/bbsdoc.php?board=' + board['name']
    html = newsm_common.request_get(url, 'GB18030', 20, 10)
    if html is None:
        print('    URL request failed: ' + url)
        return
    # print(html)

    # docWriter('Python',284,96499,0,0,3218,96528,'/groups/comp.faq/Python',1,1);
    result = re.compile('docWriter\(\'' + board['name'] + '\',(\d+),(\d+),(\d+),(\d+),(\d+),(\d+),\'([^\']+)\',(\d+),(\d+)\)').search(html)
    if result is None:
        print('Not matched')
        return
    # print(result.group())
    pages = int(result.group(5))
    boardId = int(result.group(1))

    tb_article = config.mongo_db['article_' + str(boardId)]
    skipped_count = 0
    new_articles = 0
    print('=== {}, {}'.format(boardId, board['name']))
    for page in range(pages, 1, -1):
        print('    {}, {}, P{}'.format(boardId, board['name'], page))
        articles = fetch_articles_list(board['name'], boardId, page)
        for article in articles:
            timeArray = time.localtime(article['created_at'])
            # print(time.strftime("%Y-%m-%d %H:%M:%S", timeArray) + ': ' + str(article['_id']) + ',' + article['title'])
            dummy = tb_article.find_one({'_id': article['_id']})
            if dummy is None:
                # Fetch the rest profiles for article
                fetch_article(article)
                tb_article.save(article)
                new_articles += 1
                # Add or update user
                if ('author' in article) and (not article['author'] == ''):
                    newsm_user.update_user(article['author'])
            else:
                skipped_count += 1
                #print('skip: ' + str(article['_id']))

        if (skipped_count > 60):
            break
    print('    New articles: {}'.format(new_articles))

def fetch_articles_list(boardName, boardId, page):
    url = config.base_url + '/bbsdoc.php?board=' + boardName + '&ftype=0&page=' + str(page)
    #print(url)
    html = newsm_common.request_get(url, 'GB18030', 20, 10)
    if html is None:
        print('URL request failed: ' + url)
        return
    # print(html)
    # c.o(1,1,'loury','m ',985656622,'[公告]同意开设&quot;Python/Python语言&quot;看版 (转载) ',0,0,0);
    result = re.compile('c\.o\((\d+),(\d+),\'([^\']+)\',\'([^\']+)\',(\d+),\'([^\']+)\',(\d+),(\d+),(\d+)\)').findall(html)

    articles = []
    if (len(result) > 0):
        for line in result:
            article = {
                '_id': str(boardId) + '.' + line[0],
                'title':line[5].strip(),
                'parent_id':str(boardId) + '.' + line[1],
                'author':line[2].strip(),
                'size':int(line[6]),
                'flag': line[3].strip(),
                'board_name': boardName.strip(),
                'board_id': boardId,
                'created_at':int(line[4])
            }
            articles.append(article)
    return articles

def fetch_article(article):
    article['title'] = newsm_common.remove_emoji(article['title'].strip())

    realId = str(article['_id'])[len(str(article['board_id'])) + 1:]
    url = config.base_url + '/bbscon.php?bid=' + str(article['board_id']) + '&id=' + realId
    html = newsm_common.request_get(url, 'GB18030', 20, 10)
    if html is None:
        print('    URL request failed: ' + url)
        return
    # print(html)
    # prints('发信人:  [FROM: 60.191.227.*]\r[m\n');o.h(0);o.t();
    # prints('发信人:  [FROM: 60.191.227.*]\r[m\n');attach('test.zip', 4227, 2059);o.h(0);o.t();
    result = re.compile(
        '(prints\(\'(.*)\'\);(attach\(\'([^\']+)\',\s*(\d+),\s*(\d+)\);){0,}o\.h\(0\);o\.t\(\);)').search(html)
    if result is None:
        print('    Not matched: {}'.format(html))
        article['content'] = ''
        article['updated_at'] = int(time.time())
        article['attachments'] = []
        return
    article['content'] = result.group(2)
    # simplifiy the content
    article['content'] = re.sub(r'\\n', '\n', article['content'])
    article['content'] = re.sub(r'\\r\[[;\d]{0,8}m', '', article['content'])
    article['content'] = re.sub(r'\\(/|"|\')', r'\1', article['content'])
    article['content'] = newsm_common.remove_emoji(article['content'])

    # extract the IP
    ip = extract_ip_from_article(article['content'])
    if (not ip is None):
        article['ip'] = ip
    else:
        article['ip'] = None

    article['updated_at'] = int(time.time())
    article['attachments'] = []
    # If there are attachments
    if not result.group(3) is None:
        # group 3 only match one occurence, so here apply the matching on group 1 again
        result = re.compile('attach\(\'([^\']+)\',\s*(\d+),\s*(\d+)\);').findall(result.group(1))
        if len(result) > 0:
            # print(result)
            for line in result:
                attachment = {
                    'name':line[0].strip(),
                    'size':int(line[1]),
                    'id':int(line[2])
                }
                article['attachments'].append(attachment)


def extract_ip_from_article(content):
    if (content is None) or (len(content) == 0):
        print('    Content is empty')
        return None
    result = re.compile('\[FROM: ([\d\.\*]+)\](\\n)+$').search(content)
    if result is None:
        return None
    else:
        return result.group(1)


