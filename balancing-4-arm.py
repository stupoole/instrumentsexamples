import numpy as np
import time
import instruments

## This script measures the resistance of each pulsing channel in an 8 arm device. The resulting resistances are left
# assigned to the bb and therefore can be used for pulsing after or the resulting assignments can be copied from the
# output into your own script.


# define all 4 opposite pairing assignments for 2 wire measurements

assignments_top = {"I+": "A", "I-": "E"}
assignments_bottom = {"I+": "C", "I-": "G"}


# a dictionary to store the values in
resistance_assigned = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0, "G": 0, "H": 0}
resistance_measured = {"A": 0, "B": 0, "C": 0, "D": 0, "E": 0, "F": 0, "G": 0, "H": 0}

# create instrument objects
switch_box = instruments.SwitchBox()
balance_box = instruments.BalanceBox()
pg = instruments.K2461()

# connect to devices
switch_box.connect(15)
balance_box.connect(17)
pg.connect()

# set k2461 ready for 1mA probe current 2 wire with nplc 2
pg.enable_2_wire_probe(500e-6, 2)
balance_box.enable_all()
balance_box.reset_resistances()
balance_box.set_resistances(resistance_assigned)
switch_box.switch(assignments_top)
time.sleep(2)
c, v = pg.read_one()
print(int(v / c))
resistance_measured["A"] = int((v / c) / 2)
resistance_measured["E"] = int((v / c) / 2)

# set first assignment
switch_box.switch(assignments_bottom)
time.sleep(2)  # delay to allow the sb to switch
c, v = pg.read_one()  # read one value
resistance_measured["C"] = int((v / c) / 2)  # store half resistance rounded down in each channel part of the pair
resistance_measured["G"] = int((v / c) / 2)


print('resistance measured = ', resistance_measured)
max_res = int(max(resistance_measured.values()) + 5)


for pin, res in resistance_measured.items():
    resistance_assigned[pin] = min(max_res - int(res), 255)

balance_box.set_resistances(resistance_assigned)

print('resistance assigned = ', resistance_assigned)


switch_box.switch(assignments_top)
time.sleep(2)  # delay to allow the sb to switch
c, v = pg.read_one()  # read one value
resistance_measured["A"] = int((v / c) / 2)  # store half resistance rounded down in each channel part of the pair
resistance_measured["E"] = int((v / c) / 2)

switch_box.switch(assignments_bottom)
time.sleep(2)
c, v = pg.read_one()
resistance_measured["C"] = int((v / c) / 2)
resistance_measured["G"] = int((v / c) / 2)


print('New resistances = ', resistance_measured)
pg.disable_probe_current()