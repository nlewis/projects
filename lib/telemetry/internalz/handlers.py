import threading
import traceback

from projects.lib.telemetry.internalz import flagz
from projects.lib.telemetry.internalz import modulez
from projects.lib.telemetry.internalz import pygcz
from projects.lib.telemetry.internalz import smapsz
from projects.lib.telemetry.internalz import threadz
from projects.lib.telemetry.internalz import varz


_HANDLERS = {}
_HANDLERS_LOCK = threading.Lock()

_DEFAULT_HANDLERS = {
    '/flagz': flagz.HandleFlagz,
    '/modulez': modulez.HandleModulez,
    '/pygcz': pygcz.HandlePygcz,
    '/smapsz': smapsz.HandleSmapsz,
    '/threadz': threadz.HandleThreadz,
    '/varz': varz.HandleVarz,
}


def RegisterHandler(path, handler):
  with _HANDLERS_LOCK:
    _HANDLERS[path] = handler


def GetHandler(path):
  with _HANDLERS_LOCK:
    return _HANDLERS.get(path)


def AllHandlers():
  with _HANDLERS_LOCK:
    return _HANDLERS.copy()


def HandleError(environ, start_response):
  formatted_exception = traceback.format_exc()
  start_response(
      '500 Internal Server Error', [('Content-Type', 'text/html')])
  yield '<html><head><title>Internal Server Error</title></head><body>'
  yield '<p><h1>Internal Server Error</h1></p>'
  yield '<pre>'
  yield formatted_exception
  yield '</pre>'
  yield '</body></html>'


def HandleHelpz(environ, start_response):
  start_response('200 OK', [('Content-Type', 'text/html')])
  yield '<html><body>'
  yield '<h2>Registered paths:</h2>'
  for path in AllHandlers():
    yield '<a href="%s">%s</a><br>' % (path, path)
  yield '</body></html>'


def RegisterDefaultHandlers():
  RegisterHandler('/helpz', HandleHelpz)

  for path, handler in _DEFAULT_HANDLERS.iteritems():
    RegisterHandler(path, handler)
