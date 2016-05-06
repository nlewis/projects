import platform
import socket
import threading
import time

CALLBACKS = []
EVENTS = dict()
LOCK = threading.Lock()


def Increment(key, increment_by=1):
  with LOCK:
    EVENTS[key] = EVENTS.get(key, 0) + increment_by


def Add(key, how_much):
  Increment(key, how_much)


def Set(key, value):
  with LOCK:
    EVENTS[key] = value


def Get(key):
  with LOCK:
    return EVENTS.get(key)


def GetEvents():
  events_copy = dict()
  with LOCK:
    events_copy.update(EVENTS)
    callbacks_copy = CALLBACKS[:]

  for key, cb in callbacks_copy:
    events_copy[key] = cb()

  return events_copy


def AddCallback(key, cb):
  with LOCK:
    CALLBACKS.append((key, cb))
