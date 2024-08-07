import argparse
import datetime as dt
import gzip
import os
import random
import time
import struct

import impress_exact_structs as ies
from constants import DATE_FMT

def main():
    p = argparse.ArgumentParser(
        description='simulate IMPRESS science data (time_slices)')
    p.add_argument(
        'data_dir',
        default='test-data',
        help='directory to save data to')
    p.add_argument(
        'num_files',
        type=int,
        default=30,
        help='number of data files to generate')
    p.add_argument(
        'seconds_per_file',
        type=int,
        default=30,
        help='number of seconds per time_slice file')
    args = p.parse_args()

    os.makedirs(args.data_dir, exist_ok=True)

    ts = int(time.time())
    for slice_num in range(args.num_files):
        time_str = dt.datetime.fromtimestamp(ts, dt.timezone.utc).strftime(DATE_FMT)
        output_file = f'{args.data_dir}/sim-x123-hist_{time_str}_0.bin.gz'
        with gzip.open(output_file, 'wb') as f:
            for sec in range(args.seconds_per_file):
                f.write(simulate_single_slice(ts))
                ts += 1

def simulate_single_slice(time_anchor: int=0) -> ies.X123NominalSpectrumStatus:
    # initialize used vars
    spectrum_size = 1024
    randomlist = [random.randint(0, 2**16 - 1) for _ in range(spectrum_size)]

    # time 
    time = struct.pack('<L', time_anchor)

    # empty status string
    status = bytes([0] * 64)

    # size of spectrum into bytes
    spectrum_sz_struct = struct.pack('<H', spectrum_size)

    # randomized spectrum
    spectrum = b''.join(struct.pack('<L', num) for num in randomlist)
    ret = time + status + spectrum_sz_struct + spectrum
    return ret

    # Normal status string below
    # AgAAABAAAAAAAAAAJ+EHAAsUAwA+FAMAandEjAAA/vwItyovAgSAAAAAABQCowABf0YAAAAAAAAAAAAAAAAAAA==

if __name__ == '__main__':
    main()
