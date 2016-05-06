import time

class WriteThruCache(object):
  def __init__(self, lifetime_secs):
    self._cache = dict()
    self._lifetime = lifetime_secs

  def Get(self, key, update_func):
    if key in self._cache:
      obj, expiry = self._cache.get(key)
      if expiry > time.time():
        return obj

    obj = update_func()

    expiry = time.time() + self._lifetime
    self._cache[key] = (obj, expiry)
    return obj

