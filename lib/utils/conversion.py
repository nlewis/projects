import os


def UserHz():
  return os.sysconf(os.sysconf_names['SC_CLK_TCK'])


def JiffiesToMs(jiffies):
  return long(jiffies) / UserHz()
