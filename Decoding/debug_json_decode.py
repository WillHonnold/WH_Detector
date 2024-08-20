import argparse
import datetime as dt
import json
import gzip
import numpy as np
import helpers as hp
import constants as umncon

# Monkeypatch JSON to output only 2 decmials
# https://stackoverflow.com/a/69056325
class RoundingFloat(float):
    __repr__ = staticmethod(lambda x: format(x, '.2f'))

json.encoder.c_make_encoder = None
json.encoder.float = RoundingFloat

def decode_hafx_debug():
    p = argparse.ArgumentParser(
        description='Decode HaFX debug files to JSON')
    p.add_argument(
        'files', nargs='+',
        help='debug files to decode to JSON')
    p.add_argument(
        'output_fn',
        help='output file name to write JSON')
    args = p.parse_args()

    data = []
    for fn in args.files:
        data += hp.read_hafx_debug(fn, gzip.open)
    
    decoded = [d.decode() for d in data]

    out = {
        'values': [d['registers'] for d in decoded]
    }
    for i in range(len(out['values'])):
        out['values'][i] = [num / 32 for num in out['values'][i]]
    with open(args.output_fn, 'w') as f:
        json.dump(out, f, indent=1)

if __name__ == "__main__":
    decode_hafx_debug()