import os
import sys

sys.excepthook = lambda t, v, tb: (sys.__excepthook__(t, v, tb),
                                   sys.stdout.flush(), os._exit(1))
print("PROBE before raise", flush=True)
raise RuntimeError("probe-deliberate")
