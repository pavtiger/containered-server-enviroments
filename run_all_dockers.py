#!/usr/bin/env python3
import pandas as pd
import os
import random
import string
import secrets
import subprocess
import argparse

from config import MEMORY_LIMIT, PIDS_LIMIT, IP_PREFIX, PORTS_PER_USER, STARTING_PORT


ap = argparse.ArgumentParser()
ap.add_argument("-i", "--import", required=False, help="Path to input folder with .tar files (generated using `export_dockers.py`)", default="")
ap.add_argument("-f", "--force", help="Create new container even if one already exists", action='store_true')
args = vars(ap.parse_args())


def generate_password(length):
    alphabet = string.ascii_letters + string.digits

    while True:
        password = ''
        for i in range(length):
            password += ''.join(secrets.choice(alphabet))

        if sum(char in string.digits for char in password) >= 2:
            break

    return password


os.system(f"docker network create --subnet={IP_PREFIX}.0/16 --opt com.docker.network.bridge.name=imain_network main_network");
print()

df = pd.read_csv('users.csv', index_col=False)
for index, row in df.iterrows():
    stdout = subprocess.check_output(['docker', 'ps', '-a', '--format', '"{{.Names}}"'])
    existing_containers = stdout.decode('UTF-8').replace('"', '').split('\n')
    if row['username'] in existing_containers:
        if args["force"]:
            os.system(f"docker stop {row['username']}")
            os.system(f"docker rm {row['username']}")
        else:
            print(f"Skipping user {row['username']} because there is already a container")
            continue  # Skip container creation

    if not isinstance(row['default_password'], str):
        default_password = generate_password(12)
    else:
        default_password = row['default_password']

    username = row['username']
    start, end = STARTING_PORT + index * PORTS_PER_USER + 1, STARTING_PORT + (index + 1) * PORTS_PER_USER - 1  # [start, end]

    if args["import"] == "":
        image_name = "template_ubuntu"
    else:
        image_name = row['username'] + "_image:latest"
        os.system(f"docker image rm {image_name}")
        os.system(f"docker import --change 'CMD [\"/usr/sbin/sshd\",\"-D\"]' {os.path.join(args['import'], row['username'] + '.tar')} {image_name}")

    cmd = f"docker run --privileged --name {username} --hostname london-silaeder-server --memory={MEMORY_LIMIT}g --pids-limit {PIDS_LIMIT} -dti -p {STARTING_PORT + index * PORTS_PER_USER}:22 -v /home/dockers/{username}:/home/{username} --net main_network --ip {IP_PREFIX}.{2 + index} {image_name}"
    print("Docker run command:", cmd)
    os.system(cmd)

    commands = [
            f"docker exec {username} /bin/sh -c 'useradd -s /bin/bash -g sudo -m {username}'",
            f"docker exec {username} /bin/sh -c 'echo \"{username}:{default_password}\" | chpasswd'",
            f"docker exec {username} /bin/sh -c 'chmod -R 755 /home'",
            f"docker exec {username} /bin/sh -c 'chown -R {username} /home'",

            f"docker exec {username} /bin/sh -c 'rm -rf /home/{username}/.zshrc'",
            f"docker exec {username} /bin/sh -c 'rm -rf /home/{username}/.oh-my-zsh'",
            f"docker exec {username} /bin/sh -c 'rm -rf /home/{username}/.p10k.zsh'",

            f"docker exec --user {username} {username} /bin/sh -c 'sh -c \"$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)\"'",  # Install oh-my-zsh

            f"docker exec --user {username} {username} /bin/sh -c 'git clone --depth=1 https://github.com/romkatv/powerlevel10k.git /home/{username}/.oh-my-zsh/custom/themes/powerlevel10k'",  # p10k install
            f"docker exec {username} /bin/sh -c \"sed 's,ZSH_THEME=[^;]*,ZSH_THEME=\\\"powerlevel10k/powerlevel10k\\\",' -i /home/{username}/.zshrc\"",
            f"docker exec {username} /bin/sh -c \"echo 'alias python=\\\"python3\\\"' >> /home/{username}/.zshrc\"",

            f"docker exec {username} /bin/sh -c 'chsh -s $(which zsh) {username}'",  # Change default shell to zsh
            ]

    if args["import"] == "":
        for command in commands:
            os.system(command)

    df.loc[index,'default_password'] = default_password
    print()  # Newline

df.to_csv('users.csv', index=False)

