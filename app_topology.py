#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import yaml
import json
import argparse
import datetime
import re

from deepdiff import DeepDiff

from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.functions.text import print_result
from nornir.core.exceptions import NornirExecutionError

os.environ['NET_TEXTFSM'] = os.path.dirname(os.path.abspath(__file__)) + '\\ntc-template\\templates\\'
TOPOLOGIES_DIR_PATH = os.path.dirname(os.path.abspath(__file__)) + '\\topologies' # каталог сохраненных топологий

def extract_hostname_from_fqdn(fqdn: str) -> str:
    """Extracts hostname from fqdn-like string

    For example, R1.cisco.com -> R1,  sw1 -> sw1"
    """
    return fqdn.split(".")[0]

def update_node(topology_data, dev='', group='edge_device', dev_cap=''):
    # Device Capability
    if 'B' in dev_cap:
        if 'R' in dev_cap:
            dev_type = "l3switch"
        else:
            dev_type = "l2switch"
    elif 'R' in dev_cap:
        dev_type = "router"
    elif 'S' in dev_cap:
        dev_type = "server"
    elif 'T' in dev_cap:
        dev_type = "phone"
    else:
        dev_type = "l3switch"

    for device in topology_data['nodes']:
        if device['host'] == dev:
            if device['group'] == 'core_device':
                return
            device['group'] = group
            return
    topology_data['nodes'].append( { 'host': dev, 'group': group, 'dev_type': dev_type } )
    return

def find_node_group(topology_data, dev='', group='core_device'):
    for device in topology_data['nodes']:
        if device['host'] == dev:
            if device['group'] == group:
                return True
            else:
                return False
    return False

def hostname_task(task, new_hostname: dict):
    try:
        hostname = task.run(netmiko_send_command, command_string="show run | i hostname")
    except  NornirExecutionError:
        print("ОШИБКА!!! в hostname_task!!!")
    m = re.search(r'^hostname\s+(\S+)\s*$', hostname.result, flags=re.MULTILINE)
    new_hostname.update( { task.host.name : m.group(1) if m else task.host } )
    return

def gather_info():
    # Сбор информации о топологии сети используя протокол LLDP
    with InitNornir(config_file="config.yaml") as nr:

        # Netmiko
        new_hostname: dict = dict()
        nr.run(hostname_task, new_hostname=new_hostname)
        lldp_table = nr.run(netmiko_send_command, command_string="show lldp neighbors", use_textfsm=True)

        # Формируем топологию в формате { nodes: [список узлов] , edges: [список соеинений] }
        # nodes: { host, group, dev_type }
        # edges: { from, to, from_interface, to_interface }
        topology_data = { 'nodes': [], 'edges': [] }
        for host in nr.inventory.hosts.keys():
            update_node(topology_data,dev=new_hostname.get(host,host),group='core_device')
            if host not in nr.data.failed_hosts:
                if isinstance(lldp_table[host][0].result, list):
                    for neighbor in lldp_table[host][0].result:
                        if not find_node_group(topology_data,dev=extract_hostname_from_fqdn(neighbor['neighbor'])):
                            update_node(topology_data,dev=extract_hostname_from_fqdn(neighbor['neighbor']),dev_cap=neighbor.get('capabilities', ''))

                            topology_data['edges'].append( {
                                                    'from': new_hostname[host],
                                                    'from_interface': neighbor['local_interface'],
                                                    'to': extract_hostname_from_fqdn(neighbor['neighbor']),
                                                    'to_interface': neighbor['neighbor_interface']
                                                    })
                        #print(json.dumps(neighbor, indent=4))
        #print(json.dumps(topology_data, indent=4))
        return topology_data

def save_topology(topology_data,timestamp):
    topology_file = os.path.join(TOPOLOGIES_DIR_PATH, '{}-{}.json'.format('topology', timestamp))
    with open(topology_file, 'w') as file:
        file.write(json.dumps(topology_data, indent=4))
    return '{}-{}.json'.format('topology', timestamp)

def compare_topologies(file1,file2):
    if os.path.isfile(file1) and os.path.isfile(file2):
        with open(file1) as json_file1, open(file2) as json_file2:    
            return DeepDiff(json.load(json_file1),json.load(json_file2),ignore_order=True)
    else:
        return False

def main():
    parser, args = get_args()

    #timestamp = datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S")

    if args.compare:
        # Сравнение двух топологий в формате JSON
        print('Сравнение двух топологий в формате JSON')
        topology_files = args.compare
        print(json.dumps(compare_topologies(topology_files[0],topology_files[1]), indent=4))
        return

    # Сбор информации по mac адресам и интерфейсам в сети
    topology_data = gather_info()

    if args.save:
        # Сохранение полученной топологии
        print('Сохранение')
        save_topology(topology_data,datetime.datetime.now().strftime("%Y_%m_%d-%H_%M_%S"))
    else:
        # Выводим на экран
        print('Вывод на экран')
        print(json.dumps(topology_data, indent=4))
    return

def get_args():
    # Парсер аргументов командной строки
    parser = argparse.ArgumentParser(description="Построение топологии сети (LLDP)")

    parser.add_argument(
        "--compare",
        action='store',
        nargs=2,
        help="Сравнение двух топологий в формате JSON"
    )

    parser.add_argument(
        "--save",
        action='store_true',
        help="Сохранение полученной топологии в формате JSON"
    )

    return parser, parser.parse_args()

if __name__ == '__main__':
    main()