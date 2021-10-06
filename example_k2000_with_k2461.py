import time
import matplotlib.pyplot as plt
import instruments

# This scripts measures the 4 wire resistance using the k2461 as a source meter.

# first create instrument objects using instruments.instrumentname()
pg = instruments.K2461()
dmm = instruments.K2000()

# Then connect to the instruments. Some need ports some need a GPIB address also
dmm.connect(4)
pg.connect()

pg.enable_2_wire_probe(100e-6, 2)  # set properties ready for measuring 2 wire voltage and apply current
time.sleep(0.1)  # wait for change to apply
dmm.prepare_measure_one(0, 2)  # prepare a single value measurement on the K2000
current, voltage = pg.read_one()  # measure a single value on K2461
volt2 = dmm.read_one()  # measure a single value on K2000
print(voltage / current, volt2 / current)
pg.disable_probe_current()  # turn off the current

pg.enable_4_wire_probe(100e-6, 2)  # set properties ready for measuring 4 wire voltage and apply current
time.sleep(0.1)  # wait for change to apply
dmm.prepare_measure_one(0, 2)  # prepare a single value measurement on the K2000
current, voltage = pg.read_one()  # measure a single value on K2461
volt2 = dmm.read_one()  # measure a single value on K2000
print(voltage / current, volt2 / current)
pg.disable_probe_current()  # turn off the current

#  todo: add code to show how to loop through N measurements using trigger