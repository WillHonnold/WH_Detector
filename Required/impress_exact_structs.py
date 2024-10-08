import base64
import ctypes
import struct
from datetime import datetime, timedelta
from astropy import units as u

# Nominal HaFX data class from C++ implemented in Python
# to make loading/decoding easier
NUM_HG_BINS = 123
HafxHistogramArray = NUM_HG_BINS * ctypes.c_uint32
class NominalHafx(ctypes.Structure):
    # do not pad the struct
    _pack_ = 1
    _fields_ = [
        ('ch', ctypes.c_uint8),
        ('buffer_number', ctypes.c_uint16),
        ('num_evts', ctypes.c_uint32),
        ('num_triggers', ctypes.c_uint32),
        ('dead_time', ctypes.c_uint32),
        ('anode_current', ctypes.c_uint32),
        ('histogram', HafxHistogramArray),
        ('time_anchor', ctypes.c_uint32),
        ('missed_pps', ctypes.c_bool)
    ]
    def to_json(self):
        units = {
            'dead_time': 'microsecond',
            'anode_current': 'nanoampere',
        }
        converters = {
            'dead_time': lambda x: ((800 * x) << u.ns).to_value(u.microsecond),
            'anode_current': lambda x: ((25 * x) << u.nanoampere).to_value(u.nanoampere),
            'ch': lambda x: ['c1', 'm1', 'm5', 'x1'][x],
            'histogram': lambda x: list(x),
            'missed_pps': lambda x: bool(x),
        }
        ret = {
            k: {
                'value': converters.get(k, lambda x: x)(getattr(self, k)),
                'unit': units.get(k, 'N/A')
            }
            for k, _ in self._fields_
        }
        return ret

class HafxHealth(ctypes.Structure):
    # no struct padding
    _pack_ = 1
    _fields_ = [
        # 0.01K / tick
        ('arm_temp', ctypes.c_uint16),
        # 0.01K / tick
        ('sipm_temp', ctypes.c_uint16),
        # 0.01V / tick
        ('sipm_operating_voltage', ctypes.c_uint16),
        ('sipm_target_voltage', ctypes.c_uint16),
        ('counts', ctypes.c_uint32),

        # clock cycles = 25ns / tick for a 40MHz clock
        ('dead_time', ctypes.c_uint32),
        # clock cycles = 25ns / tick for a 40MHz clockh
        ('real_time', ctypes.c_uint32),
    ]

    def to_json(self):
        units = {
            'arm_temp': 'Kelvin',
            'sipm_temp': 'Kelvin',
            'sipm_operating_voltage': 'volt',
            'sipm_target_voltage': 'volt',
            'counts': 'count',
            'dead_time': 'microsecond',
            'real_time': 'microsecond'
        }
        converters = {
            'arm_temp': lambda x: (0.01 * x << u.K).to_value(u.Kelvin),
            'sipm_temp': lambda x: (0.01 * x << u.K).to_value(u.Kelvin),
            'sipm_operating_voltage': lambda x: (0.01 * x << u.volt).to_value(u.volt),
            'sipm_target_voltage': lambda x: (0.01 * x << u.volt).to_value(u.volt),
            'dead_time': lambda x: (x << (25 * u.ns)).to_value(u.us),
            'real_time': lambda x: (x << (25 * u.ns)).to_value(u.us),
        }
        return {
            k: {
                'value': converters.get(k, lambda x: x)(getattr(self, k)),
                'unit': units[k]
            }
            for k, _ in self._fields_
        }


class X123Health(ctypes.Structure):
    _fields_ = [
        # 1 degC / tick
        ('board_temp', ctypes.c_int8),
        # 0.5V / tick
        ('det_high_voltage', ctypes.c_int16),
        # 0.1K / tick
        ('det_temp', ctypes.c_uint16),
        ('fast_counts', ctypes.c_uint32),
        ('slow_counts', ctypes.c_uint32),

        # 1ms / tick
        ('accumulation_time', ctypes.c_uint32),
        ('real_time', ctypes.c_uint32),
    ]
    # no struct padding
    _pack_ = 1

    def to_json(self):
        units = {
            'board_temp': 'Kelvin',
            'det_high_voltage': 'volt',
            'det_temp': 'Kelvin',
            'fast_counts': 'count',
            'slow_counts': 'count',
            'accumulation_time': 'millisecond',
            'real_time': 'millisecond'
        }
        converters = {
            'board_temp': lambda x: (x << u.deg_C).to_value(u.Kelvin, equivalencies=u.temperature()),
            'det_high_voltage': lambda x: (0.5*x << u.volt).to_value(u.volt)
        }
        return {
            k: {
                'value': converters.get(k, lambda x: x)(getattr(self, k)),
                'unit': units[k]
            }
            for k, _ in self._fields_
        }


# In case we want to load health data into Python,
# which we almost certainly do want to,
# we have this class! :-)
class DetectorHealth(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ('timestamp', ctypes.c_uint32),
        ('c1', HafxHealth),
        ('m1', HafxHealth),
        ('m5', HafxHealth),
        ('x1', HafxHealth),
        ('x123', X123Health)
    ]

    def to_json(self):
        return {'timestamp': self.timestamp} | {
            k: getattr(self, k).to_json() for (k, _) in self._fields_[1:]
        }


class X123NominalSpectrumStatus:
    def __init__(self, timestamp_seconds: int, count_histogram: list[int], status: bytes):
        self.timestamp = timestamp_seconds
        self.histogram = count_histogram
        # Encode to base64 for easy storage
        self.status_b64 = base64.b64encode(status).decode('utf-8')

    def to_json(self):
        return {
            'timestamp': self.timestamp,
            'histogram': list(self.histogram),
            'status_b64': self.status_b64,
        }


class X123Debug:
    def __init__(self, debug_type: int, debug_bytes: bytes):
        self.type = debug_type
        self.bytes = debug_bytes

    def decode(self) -> dict[str, object]:
        '''
        Decode the contained bytes into something more useful
        '''
        TYPE_MAP = [
            'histogram',
            'diagnostic',
            'ascii-settings'
        ]
        DECODE_MAP = [
            self._decode_histogram,
            self._decode_diagnostic,
            self._decode_ascii
        ]

        return {
            'type': TYPE_MAP[self.type],
            'data': DECODE_MAP[self.type]()
        }

    def _decode_histogram(self):
        # Last 64B are status data (spectrum + status packet)
        status_start = len(self.bytes) - 64
        data, status = self.bytes[:status_start], self.bytes[status_start:]

        # Each histogram entry is 3x uint32_t
        histogram = []
        for i in range(0, len(data), 3):
            histogram.append(
                data[i] |
                (data[i+1] << 8) |
                (data[i+2] << 16)
            )

        return {
            'status': base64.b64encode(status).decode('utf-8'),
            'histogram': histogram
        }

    def _decode_diagnostic(self):
        return base64.b64encode(self.bytes).decode('utf-8')

    def _decode_ascii(self):
        # the X-123 buffer comes out as padded with a bunch of zeros at the end
        first_null = self.bytes.index(0)
        # ASCII settings string is...ASCII already
        return self.bytes[:first_null].decode('utf-8')


class HafxDebug:
    # Order matters here (decoding enum)
    TYPE_MAP = [
        'arm_ctrl',
        'arm_cal',
        'arm_status',
        'fpga_ctrl',
        'fpga_statistics',
        'fpga_weights',
        'histogram',
        'listmode',
    ]
    # Taken from MDS documentation
    # https://www.bridgeportinstruments.com/products/software/wxMCA_doc/documentation/english/mds/mca3k/introduction.html
    DECODE_MAP = [
        '<12f',
        '<64f',
        '<7f',
        '<16H',
        '<16L',
        '<1024H',
        '<4096L',
        '<1024H',
        # TODO add scope trace
    ]
        

    def __init__(self, debug_type: int, debug_bytes: bytes):
        self.type = debug_type
        self.bytes = debug_bytes

    def decode(self) -> dict[str, object]:
        return {
            'type': HafxDebug.TYPE_MAP[self.type],
            'registers': list(struct.unpack(
                HafxDebug.DECODE_MAP[self.type], self.bytes))
        }