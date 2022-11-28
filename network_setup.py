import pandas as pd
import numpy as np
import os
import random
import string
import subprocess


GENERATE_PASSWORDS = False


df = pd.read_csv('users_with_passwords.csv')
for index, row in df.iterrows():
    username = row['username']
    start, end = (index + 1) * 1000 + 1, (index + 1) * 1000 + 999
 
    docker_ip = f"172.17.0.{2 + index}"
    print(docker_ip)

    networking_commands = [
        f"iptables -A DOCKER -t nat -p tcp -m tcp ! -i docker0 --dport {start}:{end} -j DNAT --to-destination {docker_ip}:{start}-{end}",
        f"iptables -A DOCKER -p tcp -m tcp -d {docker_ip}/32 ! -i docker0 -o docker0 --dport {start}:{end} -j ACCEPT",
        f"iptables -A POSTROUTING -t nat -p tcp -m tcp -s {docker_ip}/32 -d {docker_ip}/32 --dport {start}:{end} -j MASQUERADE"
    ]

    for command in networking_commands:
        os.system(command)

df.to_csv('users_with_passwords.csv')

