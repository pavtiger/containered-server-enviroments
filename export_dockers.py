import pandas as pd
import os


df = pd.read_csv('users.csv', index_col=False)
for index, row in df.iterrows():
    print(f"Starting export for {row['username']}")
    os.system(f"docker export {row['username']} > {os.path.join('exports', row['username'] + '.tar')}")

