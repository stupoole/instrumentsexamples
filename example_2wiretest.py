import instruments
import time
import numpy as np
from tkinter import filedialog as dialog

assignments_0 = {"I+": "A", "I-": "E"}
assignments_45 = {"I+": "B", "I-": "F"}
assignments_90 = {"I+": "C", "I-": "G"}
assignments_135 = {"I+": "D", "I-": "H"}
probe_current = 100e-6

R = np.zeros(4)
sb = instruments.SwitchBox()
pg = instruments.K2461()
sb.connect(8)
pg.connect()

sb.switch(assignments_0)
time.sleep(0.2)
pg.enable_2_wire_probe(probe_current)
time.sleep(0.2)
c, v = pg.read_one()
R[0] = v / c
pg.disable_probe_current()
time.sleep(0.2)

sb.switch(assignments_45)
time.sleep(0.2)
pg.enable_2_wire_probe(probe_current)
time.sleep(0.2)
c, v = pg.read_one()
R[1] = v / c
pg.disable_probe_current()
time.sleep(0.2)

sb.switch(assignments_90)
time.sleep(0.2)
pg.enable_2_wire_probe(probe_current)
time.sleep(0.2)
c, v = pg.read_one()
R[2] = v / c
pg.disable_probe_current()
time.sleep(0.2)

sb.switch(assignments_135)
time.sleep(0.2)
pg.enable_2_wire_probe(probe_current)
time.sleep(0.2)
c, v = pg.read_one()
R[3] = v / c
pg.disable_probe_current()
time.sleep(0.2)

print('Resistances: \n', R)
pg.disable_probe_current()
name = dialog.asksaveasfilename(title='Save')
if name:  # if a name was entered, don't save otherwise
    if name[-4:] != '.txt':  # add .txt if not already there
        name = f'{name}.txt'
    np.savetxt(name, R, newline='\r\n', delimiter='\t')  # save
    print(f'Data saved as {name}')
else:
    print('Data not saved')