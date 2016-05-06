import gflags
import sys
import threading
import traceback
import wsgiref.simple_server

from projects.lib.concurrency import threadlib
from projects.lib.telemetry import default_variables
from projects.lib.telemetry.internalz import handlers
from projects.lib.telemetry.internalz import pygcz
from projects.lib.telemetry.internalz import smapsz
from projects.lib.telemetry.internalz import threadz
from projects.lib.telemetry.internalz import varz


FLAGS = gflags.FLAGS

gflags.DEFINE_integer('telemetry_port', 8080, 'Port for telemetry server.')


def TelemetryHandler(environ, start_response):
  handler = handlers.GetHandler(environ['PATH_INFO'])

  if handler is None:
    start_response('404 Not Found', [('Content-Type', 'text/plain')])
    yield 'Path not found: %s' % (environ['PATH_INFO'],)
    return

  try:
    response = handler(environ, start_response)
  except Exception as e:
    print 'Exception!'
    response = handlers.HandleError(environ, start_response)

  for line in response:
    yield line


class TelemetryServer(threadlib.Thread):
  def __init__(self):
    super(TelemetryServer, self).__init__()
    self.daemon = True
    self.name = 'TelemetryServer'

  def run(self):
    default_variables.InitDefaultVariables()
    handlers.RegisterDefaultHandlers()
    self.ServeForever()

  def ServeForever(self, port=None):
    if port is None:
      port = FLAGS.telemetry_port

    self.server = wsgiref.simple_server.make_server('', port, TelemetryHandler)
    self.server.serve_forever(poll_interval=0.5)

  def Shutdown(self):
    self.server.shutdown()
