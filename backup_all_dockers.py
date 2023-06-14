#!/usr/bin/env python3
import os
import subprocess
import pandas as pd

from config import BACKUP_DIR


df = pd.read_csv('users.csv', index_col=False)
for index, row in df.iterrows():
    stdout = subprocess.check_output(['docker', 'ps', '-a', '--format', '"{{.Names}}"'])
    existing_containers = stdout.decode('UTF-8').replace('"', '').split('\n')
    if row['username'] in existing_containers:
        cmd = f"docker export {row['username']} | gzip > {os.path.join(BACKUP_DIR, row['username'].replace(' ', '_'))}.tar"
        os.system(cmd)
        print(f"backup for user {row['username']} complete")

