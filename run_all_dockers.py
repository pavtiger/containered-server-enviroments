#!/usr/bin/env python3
import pandas as pd
import os
import random
import string
import secrets

from config import GENERATE_PASSWORDS, MEMORY_LIMIT, PIDS_LIMIT


def generate_password(length):
    alphabet = string.ascii_letters + string.digits

    while True:
        password = ''
        for i in range(length):
            password += ''.join(secrets.choice(alphabet))

        if sum(char in string.digits for char in password) >= 2:
            break

    return password


os.system("docker network create --subnet=172.19.0.0/16 --opt com.docker.network.bridge.name=imain_network main_network");

df = pd.read_csv('users_with_passwords.csv', index_col=False)
for index, row in df.iterrows():
    if GENERATE_PASSWORDS:
        default_password = generate_password(12)
    else:
        default_password = row['default_password']

    username = row['username']
    start, end = (index + 1) * 1000 + 1, (index + 1) * 1000 + 999
    
    cmd = f"docker run --name {username} --memory={MEMORY_LIMIT}g --pids-limit {PIDS_LIMIT} -dti -p {(index + 1) * 1000}:22 -v /home/dockers/{username}:/home/{username} --net main_network --ip 172.19.0.{2 + index} template_ubuntu"
    print(cmd)
    os.system(cmd)

    commands = [
            f"docker exec {username} /bin/sh -c \"useradd -s /bin/bash -g sudo -m {username}\"",
            f"docker exec {username} /bin/sh -c \"echo \"{username}:{default_password}\" | chpasswd\"",
            f"docker exec {username} /bin/sh -c \"chmod -R 755 /home\"",
            f"docker exec {username} /bin/sh -c \"chown -R {username} /home\"",

            f"docker exec {username} /bin/sh -c \"mv /home/.p10k.zsh /home/{username}/\"",
            f"docker exec {username} /bin/sh -c \"mv /home/.zshrc /home/{username}\"",
            f"docker exec {username} /bin/sh -c \"mv /home/.oh-my-zsh /home/{username}\"",
            f"docker exec {username} /bin/sh -c \"chsh -s $(which zsh) {username}\""
            ]

    for command in commands:
        os.system(command)

    df.loc[index,'default_password'] = default_password

df.to_csv('users_with_passwords.csv', index=False)

