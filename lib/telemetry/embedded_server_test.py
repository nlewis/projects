#!/usr/bin/python -B

import time

from google.apputils import app
from projects.lib.base import logging
from projects.lib.concurrency import threadlib
from projects.lib.telemetry import embedded_server


class SleepThread(threadlib.Thread):
  def run(self):
#    logging.info('SleepThread running')
    time.sleep(999)


def main(unused_argv):
  sleeper = SleepThread()
  sleeper.daemon = True
  sleeper.start()

  telemetry_server = embedded_server.TelemetryServer()
  telemetry_server.start()

  time.sleep(10)
  telemetry_server.Shutdown()


if __name__ == '__main__':
  app.run()
