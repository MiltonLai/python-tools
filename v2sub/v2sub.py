#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import sys
import os
import requests
import base64
import json
import subprocess
import re

v2ray_service_config_path = '/etc/v2ray/config.json'


def check_privilege():
    print('Checking sudo privilege...')
    euid = os.geteuid()
    if euid != 0:
        args = ['sudo', sys.executable] + sys.argv + [os.environ]
        os.execlpe('sudo', *args)


euid = os.geteuid()
if euid != 0:
    echo = '''[0]Generate config.json only
[1]Overwrite the configs and restart v2ray service\n
Please input your choice: [0]'''
    mode = input(echo)
    if mode == '1':
        check_privilege()

this_path = os.path.dirname(__file__)
conf_path = os.path.join(this_path, 'v2sub.conf')
if not os.path.exists(conf_path):
    open(conf_path, 'w+')

with open(conf_path, 'r') as conf_file:
    try:
        configs = json.load(conf_file)
        print('Loaded configs from file: {}'.format(conf_path))
    except json.decoder.JSONDecodeError:
        print('File {} is not a valid config file'.format(conf_path))
        configs = None

if configs is None or len(configs) == 0:
    print('The configuration is empty, please input the necessary information')
    configs = {
        'subscribe_url':    input('Subscription URL：'),
        'local_port':       int(input('Local port：'))
    }
    with open(conf_path, 'w') as conf_file:
        json.dump(configs, conf_file, indent=2)

print('Subscribed URL: {}, local port:{}\n'.format(configs['subscribe_url'], configs['local_port']))
print('Reading server nodes...\n')
node_strings = base64.b64decode(requests.get(configs['subscribe_url']).content).splitlines()
nodes = {}
for i in range(len(node_strings)):
    node = json.loads(base64.b64decode(bytes.decode(node_strings[i]).replace('vmess://', '')))
    print('[{:>3}] {:25} {:30}:{}'.format(i, node['ps'], node['add'], node['port']))
    nodes[i] = node

while True:
    node_index = int(input('\nPlease input the selected node: '))
    subprocess.call('ping ' + nodes[node_index]['add'] + ' -c 3 -w 10', shell=True)
    if re.search('[yesYES]', input('Do you confirm using this node？[y/N]')):
        break

v2ray_config = {
    "policy": None,
    "log": {
        "loglevel": "warning",
        "access": "/var/log/v2ray/access.log",
        "error": "/var/log/v2ray/error.log"
    },
    "inbound": {
        "tag": "proxy",
        "port": configs['local_port'],
        "listen": "127.0.0.1",
        "protocol": "socks",
        "sniffing": {
            "enabled": True,
            "destOverride": [
                "http",
                "tls"
            ]
        },
        "settings": {
            "auth": "noauth",
            "udp": True,
            "ip": None,
            "address": None,
            "clients": None
        }
    },
    "outbounds": [
        {
            "tag": "proxy",
            "protocol": "vmess",
            "settings": {
                "vnext": [
                    {
                        "address": nodes[node_index]['add'],
                        "port": int(nodes[node_index]['port']),
                        "users": [
                            {
                                "id": nodes[node_index]['id'],
                                "alterId": nodes[node_index]['aid'],
                                "email": "t@t.tt",
                                "security": "auto"
                            }
                        ]
                    }
                ],
                "servers": None,
                "response": None
            },
            "streamSettings": {
                "network": nodes[node_index]['net'],
                "security": None,
                "tlsSettings": None,
                "tcpSettings": None,
                "kcpSettings": None,
                "wsSettings": {
                    "connectionReuse": True,
                    "path": nodes[node_index]['path'],
                    "headers": {
                        "Host": nodes[node_index]['host']
                    }
                },
                "httpSettings": None,
                "quicSettings": None
            },
            "mux": {
                "enabled": True,
                "concurrency": 8
            }
        },
        {
            "tag": "direct",
            "protocol": "freedom",
            "settings": {
                "vnext": None,
                "servers": None,
                "response": None
            },
            "streamSettings": None,
            "mux": None
        },
        {
            "tag": "block",
            "protocol": "blackhole",
            "settings": {
                "vnext": None,
                "servers": None,
                "response": {
                    "type": "http"
                }
            },
            "streamSettings": None,
            "mux": None
        }
    ],
    "stats": None,
    "api": None,
    "dns": None,
    "routing": {
        "domainStrategy": "IPIfNonMatch",
        "rules": [
            {
                "type": "field",
                "port": None,
                "inboundTag": [
                    "api"
                ],
                "outboundTag": "api",
                "ip": None,
                "domain": None
            }
        ]
    }
}

v2ray_conf_path = os.path.join(this_path, 'config.json')
with open(v2ray_conf_path, 'w') as v2ray_conf_file:
    json.dump(v2ray_config, v2ray_conf_file, indent=2)
    print('Config file generated: {}'.format(v2ray_conf_path))

if re.search('[yesYES]', input('Do you want to apply the change and restart service？[y/N]')):
    if os.path.exists(v2ray_service_config_path):
        print('Backup existing config file {}'.format(v2ray_service_config_path))
        os.popen('cp {} {}'.format(v2ray_service_config_path, os.path.join(this_path, 'config.json.bak')))
    print('Apply new config file')
    os.popen('cp {} {}'.format(v2ray_conf_path, v2ray_service_config_path))
    print('Restart v2ray service')
    subprocess.call('systemctl restart v2ray.service', shell=True)

print('Done')
exit()
