#!/usr/bin/python3
# -*- coding: UTF-8 -*-

import base64
import json
import os
import os.path as path
import re
import requests
import signal
import subprocess
import sys
import time

BASE_DIR = path.dirname(path.abspath(__file__))
CONF_PATH = path.join(BASE_DIR, 'v2sub.conf')
V2_CONF_PATH = path.join(BASE_DIR, 'config.json')
V2_PATH = '/usr/bin/v2ray/v2ray'

def env_check():
    if not path.exists(V2_PATH):
        print('Can not find v2ray executable at {}'.format(V2_PATH))
        exit(1)


def signal_handler(sig, frame):
    print('Terminating the process')
    sys.exit(0)


def kill_process():
    proc = subprocess.Popen(['pgrep', 'v2ray'], stdout=subprocess.PIPE)
    for pid in proc.stdout:
        print('Killing existing process {}'.format(pid.strip()))
        os.kill(int(pid), signal.SIGTERM)
        time.sleep(3)
        # Check if the process that we killed is alive.
        try:
            os.kill(int(pid), 0)
            raise Exception('wasn\'t able to kill the process')
        except OSError as ex:
            continue


def init_configs():
    configs = {
        'subscribe_url': '',
        'local_port': 1080,
        'nodes': []
    }
    return configs


def print_nodes(nodes):
    for i in nodes:
        node = nodes[i]
        print('[{:>3}] {:25} {:30}:{}'.format(i, node['ps'], node['add'], node['port']))


def load_configs():
    print('Loading configs from {} ...'.format(CONF_PATH), end='')
    if not path.exists(CONF_PATH):
        print('Not found, initializing...', end='')
        with open(CONF_PATH, 'w') as conf_file:
            try:
                json.dump(init_configs(), conf_file, indent=2)
                print('Initialized')
            except json.decoder.JSONDecodeError:
                print('Failed in creating config file')
                exit(1)

    with open(CONF_PATH, 'r') as conf_file:
        try:
            configs = json.load(conf_file)
            print('Done')
        except json.decoder.JSONDecodeError:
            print('Not a valid config file')
            configs = init_configs()

    return configs


def save_configs(configs):
    with open(CONF_PATH, 'w') as conf_file:
        try:
            json.dump(configs, conf_file, indent=2)
        except json.decoder.JSONDecodeError:
            print('Failed in saving config file {}'.format(CONF_PATH))


def edit_configs(configs):
    configs['subscribe_url'] = input('Enter subscription URL：[{}]'.format(configs['subscribe_url'])) or configs['subscribe_url']
    configs['local_port'] = int(input('Enter local port：[{}]'.format(configs['local_port'])) or str(configs['local_port']))
    configs['nodes'] = []
    save_configs(configs)


def reimport_nodes(subscribe_url):
    print('Reading server nodes... ', end='')
    node_strings = base64.b64decode(requests.get(subscribe_url).content).splitlines()
    print('Done')
    nodes = {}
    for i in range(len(node_strings)):
        node = json.loads(base64.b64decode(bytes.decode(node_strings[i]).replace('vmess://', '')))
        nodes[str(i)] = node
    return nodes


'''
        Main Program
'''
signal.signal(signal.SIGINT, signal_handler)
env_check()
configs = load_configs()
if configs['subscribe_url'] == '':
    print('The configuration is empty, please input the necessary information')
    edit_configs(configs)

if len(configs['nodes']) == 0:
    configs['nodes'] = reimport_nodes(configs['subscribe_url'])
    save_configs(configs)

print('Subscribed URL: {}\nLocal port:{}\n'.format(configs['subscribe_url'], configs['local_port']))
print_nodes(configs['nodes'])

echo = '\n[E] Edit config file\n[R] Reimport server nodes\n[S] Select a node to start\n[T] Terminate the existing process\n\nPlease input your choice: [S]'

while True:
    mode = input(echo) or 'S'
    if mode == 'E' or mode == 'e':
        edit_configs(configs)
        configs['nodes'] = reimport_nodes(configs['subscribe_url'])
        print_nodes(configs['nodes'])
        save_configs(configs)
    elif mode == 'R' or mode == 'r':
        configs['nodes'] = reimport_nodes(configs['subscribe_url'])
        print_nodes(configs['nodes'])
        save_configs(configs)
    elif mode == 'T' or mode == 't':
        kill_process()
        exit(0)
    else:
        break


nodes = configs['nodes']
while True:
    node_index = input('\nPlease input the selected node: ')
    subprocess.call('ping ' + nodes[node_index]['add'] + ' -c 3 -w 10', shell=True)
    if re.search('[yesYES]', input('Do you confirm using this node? [y/N]')):
        break

v2ray_config = {
    "policy": None,
    "log": {
        "loglevel": "info",
        "access": path.join(BASE_DIR, 'access.log'),
        "error": path.join(BASE_DIR, 'error.log')
    },
    "inbounds": [{
        # Tag of the inbound proxy. May be used for routing.
        "tag": "socks-inbound",
        # Port to listen on. You may need root access if the value is less than 1024.
        "port": configs['local_port'],
        # IP address to listen on. Change to "0.0.0.0" to listen on all network interfaces.
        "listen": "127.0.0.1",
        # Protocol name of inbound proxy.
        "protocol": "socks",
        # Settings of the protocol. Varies based on protocol.
        "settings": {
            "auth": "noauth",
            "udp": True,
            "ip": "127.0.0.1"
        },
        # Enable sniffing on TCP connection.
        "sniffing": {
            "enabled": True,
            # Target domain will be overriden to the one carried by the connection, if the connection is HTTP or HTTPS.
            "destOverride": ["http", "tls"]
        }
    }],
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
                # Bypass access to private IPs.
                "type": "field",
                "ip": [
                    "0.0.0.0/8",
                    "10.0.0.0/8",
                    "127.0.0.0/8",
                    "172.16.0.0/12",
                    "192.168.0.0/16",
                    "::1/128",
                    "fc00::/7",
                    "fe80::/10"
                ],
                "outboundTag": "direct"
            },
            {
                # Bypass domestic domains
                "type": "field",
                "domain": [
                    "domain:baidu.com",
                    "domain:bdstatic.com",
                    "domain:baidustatic.com",
                    "domain:qq.com",
                    "domain:sogou.com",
                    "domain:sogoucdn.com",
                    "domain:newsmth.net",
                    "domain:cnblogs.com",
                    "domain:right.com.cn"
                ],
                "outboundTag": "direct"
            }
        ]
    }
}

with open(V2_CONF_PATH, 'w') as v2ray_conf_file:
    json.dump(v2ray_config, v2ray_conf_file, indent=2)
    print('Config file generated: {}'.format(V2_CONF_PATH))


kill_process()
print('Starting v2ray service...\n')
subprocess.Popen([V2_PATH, '-c', V2_CONF_PATH])
