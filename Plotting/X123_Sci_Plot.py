import argparse
import gzip
import os

import matplotlib.pyplot as plt
import numpy as np
import json
import helpers, constants

def main():
    p = argparse.ArgumentParser(
        description='Take in a folder of IMPRESS data and produce some nice plots')
    p.add_argument('json_file', help='folder containing .bin.gz IMPRESS "Level0" files')

    args = p.parse_args()

    # data = []
    # files = os.listdir(args.data_folder)
    # for fn in sorted(files):
    #     if not (fn.startswith('x123-sci')):
    #         continue
    #     data += helpers.read_x123_sci(f'{args.data_folder}/{fn}', gzip.open)
    
    # hist = [0] * 1024
    # for i in range(len(data)):
    #     for j in range(1024):
    #         hist[j] += data[i].histogram[j]

    args = p.parse_args()
    with open(args.json_file, 'r') as f:
        data = json.loads(f.read())
    hist = [0] * 1024
    for i in range(len(data)-1):
        for j in range(1024):
            hist[j] += data[i+1]['histogram'][j]

    fig, ax = plt.subplots(layout='constrained')
    adc_bins = list(range(1025))
    ax.stairs(hist, adc_bins)
    ax.set(
        xlabel='Bridgeport ADC bin',
        ylabel='Counts',
        title='IMPRESS spectrum'
    )
    #ax.set_yscale('log')
    plt.show()


if __name__ == '__main__':
    main()