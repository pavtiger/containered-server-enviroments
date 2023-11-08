#!/usr/bin/env python3
import pandas as pd
import numpy as np
import os
import random
import string
import secrets
import subprocess
import argparse
import json

from config import MEMORY_LIMIT, PIDS_LIMIT, IP_PREFIX, PORTS_PER_USER, STARTING_PORT, NETWORK_NAME, DEBUG_MODE


ap = argparse.ArgumentParser()
ap.add_argument("-i", "--import", required=False, help="Path to input folder with .tar files (generated using `export_dockers.py`)", default="")
ap.add_argument("-f", "--force", help="Create new container even if one already exists", action='store_true')
ap.add_argument("-n", "--network", help="Setup only network (iptables)", action='store_true')
ap.add_argument("-d", "--docker", help="Setup only docker containers", action='store_true')
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


os.system(f"docker network create --subnet={IP_PREFIX}.0/16 --opt com.docker.network.bridge.name={NETWORK_NAME} main_network");
print()

df = pd.read_csv('users.csv', index_col=False)
df = df.dropna(subset=["username"])

if not args["network"]:
    for index, row in df.iterrows():
        lines = subprocess.check_output(['docker', 'ps', '-a', '--format', 'json']).decode('UTF-8').split('\n')

        containers_info = dict()
        for line in lines:
            if line != "":
                json_docker = json.loads(line)
                containers_info[json_docker["Names"]] = json_docker


        if row['username'] in containers_info:
            if args["force"]:
                os.system(f"docker stop {row['username']}")
                os.system(f"docker rm {row['username']}")
            else:
                print(f"Skipping user {row['username']} because there is already a container")
                status =  containers_info[row["username"]]["Status"].split()[0]
                if status == "Exited":
                    print(f"Starting container for user {row['username']}")
                    os.system(f"docker start {row['username']}")


                continue  # Skip container creation

        if not isinstance(row['default_password'], str):
            default_password = generate_password(12)
        else:
            default_password = row['default_password']

        username = row['username']
        connection_port = int(STARTING_PORT + index * PORTS_PER_USER)

        if args["import"] == "":
            image_name = "template_ubuntu"
        else:
            image_name = row['username'] + "_image:latest"
            os.system(f"docker image rm {image_name}")
            os.system(f"docker import --change 'CMD [\"/usr/sbin/sshd\",\"-D\"]' {os.path.join(args['import'], row['username'] + '.tar')} {image_name}")

        cmd = f"docker run --privileged --name {username} --hostname london-silaeder-server --restart always --memory={MEMORY_LIMIT}g --pids-limit {PIDS_LIMIT} -dti -p {connection_port}:22 -v /home/dockers/{username}:/home/{username} --net main_network --ip {IP_PREFIX}.{2 + index} {image_name}"
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
                f"docker exec {username} /bin/sh -c 'chmod 666 /var/run/docker.sock'",
                ]

        if args["import"] == "":
            for command in commands:
                os.system(command)

        df.loc[index,'connection_port'] = connection_port
        df.loc[index,'default_password'] = default_password
        print()  # Newline


if not args["docker"]:
    for index, row in df.iterrows():
        username = row['username']
        start, end = int(STARTING_PORT + index * PORTS_PER_USER + 1), int(STARTING_PORT + (index + 1) * PORTS_PER_USER - 1)  # [start, end]
        df.loc[index,'first_available_port'] = start
        df.loc[index,'last_available_port'] = end

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


df.to_csv('users.csv', index=False)

