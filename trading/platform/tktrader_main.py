#!/usr/bin/python -B

import signal
import sys
import time

from google.apputils import app
from projects.lib.telemetry import embedded_server
from projects.lib.base import logging


class TkTrader(object):

  def SigIntHandler(self, unused_signal, unused_frame):
    logging.info('Shutting down')
    self.telemetry_server.Shutdown()
    self.telemetry_server.join()
    sys.exit(0)

  def Main(self):
    self.telemetry_server = embedded_server.TelemetryServer()
    self.telemetry_server.start()

    signal.signal(signal.SIGINT, self.SigIntHandler)

    logging.info('Serving...')
    time.sleep(600)


def main(unused_argv):
  tktrader = TkTrader()
  tktrader.Main()

if __name__ == '__main__':
  app.run()
