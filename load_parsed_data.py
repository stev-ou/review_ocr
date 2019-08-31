import numpy as np
import pandas as pd
import os
from tqdm import tqdm
from pprint import pprint

def load_parsed_data(file):
    with open(file, "r") as f:
        lines = f.readlines()
    objs = []
    for line in tqdm(lines):
        obj = eval(line)
        objs.append(obj)
    return objs
        
def convert_parsed_files_to_df():
    files = ["ForkPoolWorker-1.txt", "ForkPoolWorker-2.txt", "ForkPoolWorker-3.txt", "ForkPoolWorker-4.txt"]
    parsed_data = []
    for file in tqdm(files):
        parsed_data += load_parsed_data(file)
    return parsed_data

if __name__ == '__main__':
    df = pd.DataFrame(convert_parsed_files_to_df())
    pprint(df[df['Subject Code']=='AME'])