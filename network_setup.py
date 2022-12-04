#!/usr/bin/env python3
import pandas as pd
import numpy as np
import os
import random
import string
import subprocess


DEBUG_MODE = False
NETWORK_NAME = "imain_network"


df = pd.read_csv('users_with_passwords.csv')
for index, row in df.iterrows():
    username = row['username']
    start, end = (index + 1) * 1000 + 1, (index + 1) * 1000 + 999
 
    docker_ip = f"172.19.0.{2 + index}"
    print(docker_ip)

    networking_commands = [
        f"sudo iptables -A DOCKER -t nat -p tcp -m tcp ! -i {NETWORK_NAME} --dport {start}:{end} -j DNAT --to-destination {docker_ip}:{start}-{end}",
        f"sudo iptables -A DOCKER -p tcp -m tcp -d {docker_ip}/32 ! -i {NETWORK_NAME} -o {NETWORK_NAME} --dport {start}:{end} -j ACCEPT",
        f"sudo iptables -A POSTROUTING -t nat -p tcp -m tcp -s {docker_ip}/32 -d {docker_ip}/32 --dport {start}:{end} -j MASQUERADE"
    ]

    for command in networking_commands:
        if DEBUG_MODE:
            print(command)
        else:
            os.system(command)

df.to_csv('users_with_passwords.csv')

