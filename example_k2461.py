import pyvisa
import numpy as np
import time
import matplotlib.pyplot as plt
import Instruments

pg = Instruments.K2461()
pg.connect()

pg.pulse_current(1e-3, 1e-3)
time.sleep(5)

# how to use buffer measurements
pg.prepare_measure_n(100e-6, 50, 2)
pg.trigger()
time.sleep(10)
time, v, c = pg.read_buffer(50)
plt.plot(time, v/c)

# how to use 2 wire single measurements the easy way
pg.enable_2_wire_probe(100e-6, 2)
c, v = pg.read_one()
print(v / c)
pg.disable_probe_current()
# how to use 4 wire single measurements the easy way
pg.enable_4_wire_probe(100e-6, 2)
c, v = pg.read_one()
print(v / c)
pg.disable_probe_current()

# The best way to do 2/4 wire measurements if using multiple Instruments.
# Set up measurement settings and then trigger a single measurement on all Instruments
# then fetch the values and process them.
pg.enable_4_wire_probe(100e-6)
pg.trigger_before_fetch()
c, v = pg.fetch_one()
print(v/c)
pg.disable_probe_current()

plt.show()


#  todo: add code to show how to loop through N measurements using trigger