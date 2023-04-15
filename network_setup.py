#!/usr/bin/env python3
import pandas as pd
import numpy as np
import os
import random
import string
import subprocess

from config import IP_PREFIX, NETWORK_NAME, DEBUG_MODE


df = pd.read_csv('users.csv')
for index, row in df.iterrows():
    username = row['username']
    start, end = (index + 1) * 1000 + 1, (index + 1) * 1000 + 999
 
    docker_ip = f"{IP_PREFIX}.{2 + index}"
    print(docker_ip)

    networking_commands = [
        f"DOCKER -t nat -p tcp -m tcp ! -i {NETWORK_NAME} --dport {start}:{end} -j DNAT --to-destination {docker_ip}:{start}-{end}",
        f"DOCKER -p tcp -m tcp -d {docker_ip}/32 ! -i {NETWORK_NAME} -o {NETWORK_NAME} --dport {start}:{end} -j ACCEPT",
        f"POSTROUTING -t nat -p tcp -m tcp -s {docker_ip}/32 -d {docker_ip}/32 --dport {start}:{end} -j MASQUERADE"
    ]

    for command in networking_commands:
        if DEBUG_MODE:
            print(command)
        else:
            process = subprocess.Popen("sudo iptables -C" + command, shell=True, stdout=subprocess.PIPE)
            process.wait()
            
            if process.returncode:  # Check if this entry is not yet created
                os.system("sudo iptables -A" + command)

df.to_csv('users.csv')

