#!/usr/bin/python -B

import threading
import time

from projects.lib.telemetry import embedded_server


class SleepThread(threading.Thread):
  def run(self):
    time.sleep(999)


def main():
  sleeper = SleepThread()
  sleeper.daemon = True
  sleeper.start()

  embedded_server.ServeForever()


if __name__ == '__main__':
  main()
