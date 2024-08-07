import json
import argparse

#%matplotlib tk

def dead_time_sum():
    p = argparse.ArgumentParser(
        description='Files to sum dead time')
    p.add_argument(
        'files', nargs='+',
        help='Name of Json files to get dead time of')
    args = p.parse_args()

    for i in range(len(args.files)):
        current_selected = args.files[i]
        with open(current_selected, 'r') as f:
            data = json.loads(f.read())
        print(sum(data['dead_time']['value']) / float(10**6))

if __name__ == '__main__':
    dead_time_sum()
        
