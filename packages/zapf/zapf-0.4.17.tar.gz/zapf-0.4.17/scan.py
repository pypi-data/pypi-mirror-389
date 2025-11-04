import logging
import sys
import time

from zapf import io, scan

logging.basicConfig(level=0)

io = io.PlcIO(sys.argv[1], logging.root)
t0 = time.time()
scan = scan.Scanner(io, logging.root)
devs = list(scan.get_devices())
print(f'Readout complete in {time.time() - t0:.1f} s')
print('Running cache queries, Ctrl-C to abort')
io.start_cache()
while True:
    time.sleep(0.5)
