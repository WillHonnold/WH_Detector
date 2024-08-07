import json
import numpy as np # array
import matplotlib.pyplot as plt #plotting
from scipy.optimize import curve_fit, minimize_scalar #used for curve fitting
import argparse
import helpers as hp
import gzip

#%matplotlib tk

def json_plot():
    p = argparse.ArgumentParser(
        description='Plot x123 Json Histograms')
    p.add_argument(
        'files', nargs='+',
        help='Name of Json files to plot. Accepts multiple for overplotting.')
    args = p.parse_args()


    fig, ax = plt.subplots()

    x123_data = []
    for i,fn in enumerate(args.files):
        x123_data += hp.read_x123_debug(fn, gzip.open)
        decoded = [xd.decode() for xd in x123_data]
        hist = decoded[i]['data']['histogram']
        hist = np.array(hist)
        bins = np.arange(hist.size + 1)

        # Plot figures
        ax.stairs(hist, bins, label=fn + ' Curve', zorder=3)  # No bkg subtract

        # Set constraints
        ax.set_xlim([0, 1024])

        ax.set_xlabel('ADC bins')
        ax.set_ylabel('Counts')

        # uncomment line below to get log graph
        # ax.set_yscale('log')

        ax.legend(loc = 'upper right', fontsize = 7)
        ax.set_title('Histogram counts vs. ADC bins')

    # uncomment line below if you want to save the figure
    #plt.savefig("linear.png")

    # Display figure
    plt.grid(True, zorder = 0, linestyle = ':')
    plt.show()


if __name__ == '__main__':
    json_plot()