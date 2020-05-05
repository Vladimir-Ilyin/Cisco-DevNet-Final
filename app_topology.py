#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import yaml
import json
import argparse
import datetime

from deepdiff import DeepDiff

from nornir import InitNornir
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.plugins.functions.text import print_result

os.environ['NET_TEXTFSM'] = os.path.dirname(os.path.abspath(__file__)) + '\\ntc-template\\templates\\'
TOPOLOGIES_DIR_PATH = os.path.dirname(os.path.abspath(__file__)) + '\\topologies' # каталог сохраненных топологий

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

def gather_info():
    # Сбор информации о топологии сети используя протокол LLDP
    with InitNornir(config_file="config.yaml") as nr:

        # Netmiko
        lldp_table = nr.run(netmiko_send_command, command_string="show lldp neighbors", use_textfsm=True)

        #print_result(lldp_table)

        # Формируем топологию в формате { nodes: [список узлов] , edges: [список соеинений] }
        # nodes:
        # id, label, title, group
        # edges:
        # from, to, id, label, title
        # arrows: {
        # from: {enabled: true, type: "image", src: "http://localhost/image/INTERFACE.png"}
        # to: {enabled: true, type: "image", src: "http://localhost/image/INTERFACE.png"}
        # }
        topology_data = { 'nodes': [], 'edges': [] }
        for host in nr.inventory.hosts.keys():
            update_node(topology_data,dev=host,group='core_device')
            for neighbor in lldp_table[host][0].result:
                if not find_node_group(topology_data,dev=neighbor['neighbor']):
                    update_node(topology_data,dev=neighbor['neighbor'],dev_cap=neighbor['capabilities'])

                    topology_data['edges'].append( {
                                            'from': host,
                                            'from_interface': neighbor['local_interface'],
                                            'to': neighbor['neighbor'],
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