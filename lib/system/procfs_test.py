#!/usr/bin/python -B

import sys
import time
from projects.lib.system import procfs


def main():
  time.sleep(65)
  print procfs.SystemUptime()
  print time.ctime(procfs.SystemStartTime())
  print procfs.ProcessUptime()
  print time.ctime(procfs.ProcessStartTime())

  time.sleep(3)

  print time.ctime(procfs.SystemStartTime())
  print time.ctime(procfs.ProcessStartTime())

  sys.exit(0)

  stat = procfs.Stat()
  for field_name in sorted(stat):
    field_value = stat[field_name]
    print '%30s: %20s (%20s)' % (field_name, field_value, type(field_value))


if __name__ == '__main__':
  main()
