import os
import time

from projects.lib.utils import conversion


_STAT_FIELDS = {
    0: ('pid', int),
    1: ('comm', str),
    2: ('state', str),
    3: ('ppid', int),
    4: ('pgrp', int),
    5: ('session', int),
    6: ('tty_nr', int),
    7: ('tpgid', int),
    8: ('flags', int),
    9: ('minflt', long),
    10: ('cminflt', long),
    11: ('majflt', long),
    12: ('cmajflt', long),
    13: ('utime', long),
    14: ('stime', long),
    15: ('cutime', long),
    16: ('cstime', long),
    17: ('ppriority', long),
    18: ('nice', long),
    19: ('num_threads', long),
    20: ('itrealvalue', conversion.JiffiesToMs),
    21: ('starttime', conversion.JiffiesToMs),
    22: ('vsize', long),
    23: ('rss', long),
    24: ('rsslim', long),
    25: ('startcode', long),
    26: ('endcode', long),
    27: ('startstack', long),
    28: ('kstkesp', long),
    29: ('kstkeip', long),
    30: ('signal', long),
    31: ('blocked', long),
    32: ('sigignore', long),
    33: ('sigcatch', long),
    34: ('wchan', long),
    35: ('nswap', long),
    36: ('cnswap', long),
    37: ('exit_signal', int),
    38: ('processor', int),
    39: ('rt_priority', int),
    40: ('policy', int),
    41: ('delayacct_blkio_ticks', long),
    42: ('guest_time', long),
    43: ('cguest_time', long),
    44: ('start_data', long),
    45: ('end_data', long),
    46: ('start_brk', long),
    47: ('end_brk', long),
    48: ('arg_start', long),
    49: ('arg_end', long),
    50: ('env_start', long),
    51: ('env_end', long),
    52: ('exit_code', long),
}


def SystemUptime():
  with open('/proc/uptime') as f:
    uptime_seconds, idle_seconds = f.read().split()
  return float(uptime_seconds)


def SystemStartTime():
  return time.time() - SystemUptime()


def ProcessUptime(pid=None, tid=None):
  return SystemUptime() - Stat(pid, tid)['starttime']


def ProcessStartTime(pid=None, tid=None):
  return time.time() - ProcessUptime(pid, tid)


def Stat(pid=None, tid=None):
  if pid is None:
    pid = os.getpid()

  if tid is None:
    stat_path = '/proc/%d/stat' % (pid,)
  else:
    stat_path = '/proc/%d/task/%d/stat' % (pid, tid)

  with open(stat_path) as f:
    stat_array = f.read().split()

  stat_dict = dict()

  for field_index, field_value in enumerate(stat_array):
    field_name, field_format = _STAT_FIELDS[field_index]
    stat_dict[field_name] = field_format(field_value)

  return stat_dict


def GetSingleStat(stat_name, pid=None, tid=None):
  return Stat(pid, tid).get(stat_name)


def NumOpenFds(pid=None):
  # File descriptors are shared between threads.
  if pid is None:
    pid = os.getpid()

  return len(os.listdir('/proc/%d/fd' % (pid,)))
