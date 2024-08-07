'''
As a command line argument, pass this script a folder 
which contains a bunch of .bin.gz "level zero" data files
from IMPRESS.
Two plots are generated:
    - a spectrogram showing the counts spectrum over time
    - a spectrum, aka the spectrogram summed along time
The 2048-to-123 Bridgeport bin mapping is undone
so the histogram ADC bins line up with the "normal"
Bridgeport bins.
'''

import argparse
import os
import json

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as ticker
import datetime
import plotting
import helpers, constants

def main():
    p = argparse.ArgumentParser(
        description='Take is json file containing histogram data and analyze in a manner similar to list mode')
    p.add_argument('json_file', help='json file containing IMPRESS data to be analyzed in a manner similar to list mode')

    args = p.parse_args()
    with open(args.json_file, 'r') as f:
        data = json.loads(f.read())
    print(len(data['histogram']['value']))
    #print(len(data['timestamp']['value']))

    fig, ax = plt.subplots(layout='constrained')

    timestamps = data['timestamp']['value']
    for i in range(len(timestamps)):
        if '.' in timestamps[i]:
            end_index = timestamps[i].index('+')  # Find the start of the timezone part
            timestamps[i] = timestamps[i][11:end_index]
        else:
            timestamps[i] = timestamps[i][11:19]
    sums = []
    for i in range(len(data['histogram']['value']) - 1):
        sums.append(sum(data['histogram']['value'][i]))
    ax.stairs(sums, timestamps)
    ax.set(
        xlabel='Time (UTC)',
        ylabel='Counts',
        title='Counts Time-o-gram'
    )
    ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=6))
    plt.show()

if __name__ == '__main__':
    main()