#!/usr/bin/python -B

import sys
import threading
import time

from google.apputils import app
from projects.lib.base import logging
from projects.lib.concurrency import periodic_task
from projects.lib.telemetry import embedded_server


def LoggerTask():
  logging.info('Task running.')


def AddSomeTasksAndWait():
  logging.info('Adding tasks')
  task_a = periodic_task.AddTask(LoggerTask)
  task_b = periodic_task.AddTask(LoggerTask)
  task_c = periodic_task.AddTask(LoggerTask)
  task_d = periodic_task.AddTask(LoggerTask)

  event = threading.Event()

  logging.info('Starting tasks')
  task_a.RunForever().Every(seconds=10).StartingNow()
  task_b.RunForever().Every(seconds=10).StartingAfter(seconds=600)
  task_c.RunOnce().StartingAfter(seconds=900)
  task_d.RunForever().Every(seconds=9000).StartingAfterEvent(event)

  logging.info('Sleeping')
  time.sleep(30)
  logging.info('Main thread triggering event')
  event.set()

  logging.info('Sleeping then terminating')
  time.sleep(600)

def main(unused_argv):
  telemetry_server = embedded_server.TelemetryServer()
  telemetry_server.start()

  try:
    AddSomeTasksAndWait()
  except KeyboardInterrupt:
    periodic_task.Shutdown()
    sys.exit(0)


if __name__ == '__main__':
  app.run()
