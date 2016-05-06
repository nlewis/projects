import gc
import os
import multiprocessing
import platform
import resource
import socket
import sys
import time


from projects.lib.system import procfs
from projects.lib.telemetry import event_collection


def InitDefaultVariables():
  event_collection.Set('argv', ' '.join(sys.argv))
  event_collection.Set('application-started-time', time.time())
  event_collection.Set('application-started-time-string', time.ctime())
  event_collection.Set('hostname', socket.gethostname())
  event_collection.Set('num-cpus', multiprocessing.cpu_count())
  event_collection.Set('platform', platform.platform())
  event_collection.Set('processor', platform.processor())
  event_collection.Set('python-version', platform.python_version())

  event_collection.AddCallback('cpu-utime', GetCPUUtime)
  event_collection.AddCallback('cpu-stime', GetCPUStime)
  event_collection.AddCallback('cpu-total', GetCPUTotal)

  event_collection.AddCallback('machine-loadavg', GetMachineLoadAvg)
  event_collection.AddCallback('machine-loadavg-5min', GetMachineLoadAvg5Min)
  event_collection.AddCallback('machine-loadavg-15min', GetMachineLoadAvg15Min)

  event_collection.AddCallback('gc-collections-gen-0', GetGCCollectionsGen0)
  event_collection.AddCallback('gc-collections-gen-1', GetGCCollectionsGen1)
  event_collection.AddCallback('gc-collections-gen-2', GetGCCollectionsGen2)

  event_collection.AddCallback('application-uptime-sec', GetAppUptime)
  event_collection.AddCallback('current-time', time.time)

  event_collection.AddCallback('num-open-fds', procfs.NumOpenFds)


def GetCPUUtime():
  return resource.getrusage(resource.RUSAGE_SELF).ru_utime


def GetCPUStime():
  return resource.getrusage(resource.RUSAGE_SELF).ru_stime


def GetCPUTotal():
  rusage = resource.getrusage(resource.RUSAGE_SELF)
  return rusage.ru_utime + rusage.ru_stime


def GetAppUptime():
  return time.time() - event_collection.Get('application-started-time')


def GetMachineLoadAvg():
  return os.getloadavg()[0]


def GetMachineLoadAvg5Min():
  return os.getloadavg()[1]


def GetMachineLoadAvg15Min():
  return os.getloadavg()[2]


def GetGCCollectionsGen0():
  return gc.get_count()[0]


def GetGCCollectionsGen1():
  return gc.get_count()[1]


def GetGCCollectionsGen2():
  return gc.get_count()[2]
