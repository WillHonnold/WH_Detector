import json
import numpy as np # array
import matplotlib.pyplot as plt #plotting
from scipy.optimize import curve_fit, minimize_scalar #used for curve fitting
import argparse

#%matplotlib tk

def json_plot():
    p = argparse.ArgumentParser(
        description='Plot Json Histograms')
    p.add_argument(
        'files', nargs='+',
        help='Name of Json files to plot')
    args = p.parse_args()

    fig, ax = plt.subplots()

    for i in range(len(args.files)):
        current_selected = args.files[i]
        print(current_selected)
        # Set name for legend
        name = str(current_selected)

        with open(current_selected, 'r') as f:
            data = json.loads(f.read())
        hist = np.array(data['histograms'][i])
        print(type(hist))
        bins = np.arange(hist.size + 1)

        # Plot figures
        ax.stairs(hist, bins, label=name + ' Curve')  # No bkg subtract

        # Set constraints
        ax.set_xlim([0, 4095])
        # ax.set_ylim([1, ylim])
        ax.set_ylim((1, None))

        ax.set_xlabel('ADC bins')
        ax.set_ylabel('Counts')

        # uncomment line below to get log graph
        # ax.set_yscale('log')

        ax.legend(loc = 'upper right')
        ax.set_title('Histogram counts vs. ADC bins')

    # uncomment line below if you want to save the figure
    #plt.savefig("linear.png")

    # Display figure
    plt.show()


if __name__ == '__main__':
    json_plot()