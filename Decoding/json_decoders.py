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


def decode_health():
    p = argparse.ArgumentParser(
        description='Decode health files to JSON')
    p.add_argument(
        'health_files', nargs='+',
        help='files to decode to JSON')
    p.add_argument(
        'output_fn',
        help='output file name to write JSON')
    args = p.parse_args()

    health_data = []
    for fn in args.health_files:
        health_data += hp.read_det_health(fn, gzip.open)

    jsonified = [hd.to_json() for hd in health_data]
    jsonified.sort(key=lambda e: e['timestamp'])
    collapsed = collapse_health(jsonified)

    processed_data = {}
    processed_data['start_time'] = collapsed['timestamp'][0]
    
    for i in ['c1', 'm1', 'm5', 'x1']:
        processed_data[i] = {}
        for j in ['arm_temp', 'sipm_temp', 'sipm_operating_voltage']:
            processed_data[i][j] = (cur_proc := {})
            cur_data = collapsed[i][j]['value']

            cur_proc['avg'] = np.mean(cur_data)
            cur_proc['min'] = min(cur_data)
            cur_proc['max'] = max(cur_data)

    processed_data['x123'] = (x123_proc := {})
    for j in ['board_temp', 'det_high_voltage', 'det_temp']:
        x123_proc[j] = (cur_proc := {})
        cur_data = collapsed['x123'][j]['value']

        cur_proc['avg'] = np.mean(cur_data)
        cur_proc['min'] = min(cur_data)
        cur_proc['max'] = max(cur_data)

    final_data = {}
    final_data['processed_data'] = processed_data
    final_data['raw_data'] = collapsed
    with open(args.output_fn, 'w') as f:
        json.dump(final_data, f, indent=1)


def decode_x123_sci():
    p = argparse.ArgumentParser(
        description='Decode X123 science files to JSON')
    p.add_argument(
        'x123_files', nargs='+',
        help='gzipped files to decode to JSON')
    p.add_argument(
        'output_fn',
        help='output file name to write JSON')
    args = p.parse_args()

    x123_data = []
    for fn in args.x123_files:
        x123_data += hp.read_x123_sci(fn, gzip.open)

    json_out = [xd.to_json() for xd in x123_data]
    json_out.sort(key=lambda e: e['timestamp'])
    with open(args.output_fn, 'w') as f:
        json.dump(json_out, f, indent=1)

def decode_x123_debug():
    p = argparse.ArgumentParser(
        description='Decode X123 science files to JSON')
    p.add_argument(
        'x123_files', nargs='+',
        help='gzipped files to decode to JSON')
    p.add_argument(
        'output_fn',
        help='output file name to write JSON')
    args = p.parse_args()

    x123_data = []
    for fn in args.x123_files:
        x123_data += hp.read_x123_debug(fn, gzip.open)

    json_out = [xd.decode() for xd in x123_data]
    with open(args.output_fn, 'w') as f:
        json.dump(json_out, f, indent=1)


def decode_hafx_debug_hist():
    p = argparse.ArgumentParser(
        description='Decode HaFX debug histograms to JSON')
    p.add_argument(
        'files', nargs='+',
        help='debug histogram files to decode to JSON')
    p.add_argument(
        'output_fn',
        help='output file name to write JSON')
    args = p.parse_args()

    data = []
    for fn in args.files:
        data += hp.read_hafx_debug(fn, gzip.open)
    
    decoded = [d.decode() for d in data]
    if any(d['type'] != 'histogram' for d in decoded):
        raise ValueError(
            "Cannot decode debug other than histograms,"
            " and at least one file given is not a histogram."
        )

    out = {
        'histograms': [d['registers'] for d in decoded]
    }
    with open(args.output_fn, 'w') as f:
        json.dump(out, f, indent=1)


def get_proper_timedelta(file_name):
    '''
    Rebinned science data will have different time deltas between events.
    This is because if we sum along the time axis, the counts in the
    spectrogram can be considered to be bounded by wider time edges.

    Make this a function so that we can update it if we change the rebinning scheme down the line.
    '''
    # File name format is: IDENT_DATE_#.extension
    identifier, date_str, _ = file_name.split('_')
    date = dt.datetime.strptime(date_str, umncon.DATE_FMT)
    slice_width = dt.timedelta(seconds= 1/32 ) 

    # if 'time' in identifier:
    #     # Add more revisions as appropriate
    #     if date >= umncon.FIRST_REVISION:
    #         return umncon.FIRST_NUM_TIMES_REBIN * slice_width
    return slice_width


def get_data_format(fn: str) -> str:
    '''
    Depending on the file naming convention used by the rebinner,
    we can either be dealing with:
        - "raw" aka full-resolution data
        - rebinned across time
        - rebinned across energy
        - rebinneda cross time and energy
    '''
    possibilities = ('time+energy', 'time', 'energy')
    for p in possibilities:
        if fn.startswith(p): return p

    # No rebinning has happened; return something useful
    return 'full_resolution'


def decode_hafx_sci():
    '''
    Decode science data from binary structures to JSON.
    Assumes:
        - The first record in the binary file has a valid UNIX timestamp
        - The time and energy rebinning has been updated in the `umndet.common.constants`

    Note that the timestamps correspond to the "left" edges of the
    times where counts are recorded.
    '''
    p = argparse.ArgumentParser(
        description='Decode HaFX science files to JSON')
    p.add_argument(
        'files', nargs='+',
        help='files to decode to JSON')
    p.add_argument(
        'output_fn',
        help='output file name to write JSON')
    args = p.parse_args()

    hafx_data = []
    time_deltas = []
    data_type = []
    for fn in args.files:
        hafx_data += (cur_data := hp.read_hafx_sci(fn, gzip.open))
        # Give as many timedeltas and data formats
        # as there are data points per file,
        # so that we can easily align them later

        #this sucks and it always 4 seconds for some reason
        time_deltas += ([get_proper_timedelta(fn)] * len(cur_data))
        data_type += [get_data_format(fn)] * len(cur_data)
    

    jsonified = [hd.to_json() for hd in hafx_data]
    # from_timestamp = lambda ts: dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc)
    # recent = from_timestamp(hafx_data[0].time_anchor)
    # times = [recent]
    # idx = 1
    # for hd in hafx_data[1:]:
    #     if hd.time_anchor != 0:
    #         recent = from_timestamp(hd.time_anchor)
    #     times.append(recent + dt.timedelta(seconds=((idx % 32) / 32)))
    #     jsonified[idx]['time_anchor']['value'] = times[idx].isoformat()
    #     jsonified[idx]['time_anchor']['unit'] = 'N/A'
    #     idx += 1
    # jsonified[0]['time_anchor']['value'] = dt.datetime.fromtimestamp(jsonified[0]['time_anchor']['value'], dt.timezone.utc).isoformat()
    # # "time bins" are 1 larger than the # of histograms we get
    # #times.append(times[-1] + dt.timedelta(seconds=1/32))




    #Default value: start of UNIX epoch
    utc_time = dt.datetime.fromtimestamp(0, dt.timezone.utc)
    for i, json_dat in enumerate(jsonified):
        frame_num = json_dat['buffer_number']['value']
        step = time_deltas[i]
        anchor = int(json_dat.pop('time_anchor')['value'])

        if anchor != 0:
            utc_time = dt.datetime.fromtimestamp(anchor, dt.timezone.utc)
        json_dat['timestamp'] = {
            'value': (utc_time + (frame_num % 32) * step).isoformat() + 'Z',
            'unit': 'N/A'
        }
        type_ = data_type[i]
        json_dat['datatype'] = {
            'value': type_,
            'unit': 'N/A'
        }
    

    #jsonified.sort(key=lambda e: e['time_anchor']['value'])
    collapsed = collapse_json(jsonified)
    with open(args.output_fn, 'w') as f:
        json.dump(collapsed, f)


def collapse_json(data: list[dict[str, object]]):
    collapse_keys = tuple(data[0].keys())
    ret = dict()

    for datum in data:
        for k in collapse_keys:
            try:
                ret[k]['value'].append(datum[k]['value'])
            except KeyError:
                ret[k] = {
                    # Only assign unit once here, not above in the `try`
                    'unit': datum[k]['unit'],
                    'value': [datum[k]['value']]
                }

    return ret


def collapse_health(dat: list[dict[str, object]]) -> list[dict[str, object]]:
    detectors = ('c1', 'm1', 'm5', 'x1', 'x123')
    ret = dict()

    for detector in detectors:
        ret[detector] = collapse_json([d[detector] for d in dat])

    ret |= {
        'timestamp': [d['timestamp'] for d in dat]
    }
    return ret

if __name__ == '__main__':
    print(" 1 for decoding health packets ")
    print(" 2 for decoding x123 science ")
    print(" 3 for hafx debug histogram ")
    print(" 4 for hafx time slice ")
    dtype = int(input("Please decode type (1-4): "))
    if dtype == 1:
        decode_health()
    elif dtype == 2:
        decode_x123_sci()
    elif dtype == 3:
        decode_hafx_debug_hist()
    elif dtype == 4:
        decode_hafx_sci()
    else:
        print("Please enter a valid decode type (1-4)")