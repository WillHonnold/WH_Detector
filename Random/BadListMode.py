import argparse
import os
import json

import matplotlib.pyplot as plt
import numpy as np
import matplotlib.ticker as ticker
import datetime
import plotting
import helpers, constants

def check_for_events(data):
    # for timestamps
    event_start = ''
    event_end = ''
    event_array = []
    loop_start = 0
    # get bkg_avg so we can confirm events are happening
    bkg_avg = get_bkg_avg(data)
    print(bkg_avg)
    print()

    # need to to not start an event immediately
    event_polarity = False

    for i in range(len(data['histogram']['value'])):

        # current total counts of this frames histogram

        current = sum(data['histogram']['value'][i])

        
        # event start
        # checks if the counts in any bin are much higher than the average of the first ~3 seconds (totally cheating)
        if ( current > (bkg_avg * 4) ) and event_start == '':
            if event_polarity == False:
                event_polarity = True
            event_start = data['timestamp']['value'][i]
            loop_start = i
            event_array.append(event_start)

        # Event end
        # Event polarity required to it so it doesn't event end on every background frame
        elif ( current < (bkg_avg * 4) ) and event_end == '':
            if event_polarity == False:
                continue
            event_end = data['timestamp']['value'][i]
            event_array.append(event_end)
            print("EVENT START: " + f'{event_start}')
            print("EVENT END: " + f'{event_end}')
            total_cts = 0
            for j in range(loop_start, i):
                total_cts += sum(data['histogram']['value'][j])
            print("TOTAL COUNTS: " + f'{total_cts}')
            print()
            event_end = ''
            event_start = ''
            event_polarity = False

        # Last bin case (can't check next bin to end event if event is happening during the last frame)
        elif i == (len(data['histogram']['value']) - 1):
            if event_polarity == False:
                continue
            event_end = data['timestamp']['value'][i]
            event_array.append(event_end)
            print("EVENT START: " + f'{event_start}')
            print("EVENT END: " + f'{event_end}')
            total_cts = 0
            for j in range(loop_start, i):
                total_cts += sum(data['histogram']['value'][j])
            print("TOTAL COUNTS: " + f'{total_cts}')
            print()
    print("~~~TOTAL EVENTS~~~")
    print(int(len(event_array)/2))
    return event_array

def get_bkg_avg(data):
    total = 0
    for i in range(100):
        total += sum(data['histogram']['value'][i])
    average = total / 100
    return average


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
    event_array = check_for_events(data)

    ax.stairs(sums, timestamps)
    ax.set(
        xlabel='Time (UTC)',
        ylabel='Counts',
        title='Counts Time-o-gram'
    )
    ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=4))

    # I plot a da lines
    for i in range(len(event_array)):
        if i % 2 != 0:
            plt.axvline(x=event_array[i], color='firebrick', linestyle='-', linewidth=1)
        else:
            plt.axvline(x=event_array[i], color='forestgreen', linestyle='-', linewidth=1)
    plt.show()

if __name__ == '__main__':
    main()