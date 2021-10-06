import instruments
import time
import numpy as np
from tkinter import filedialog as dialog

sb = instruments.SwitchBox()
pg = instruments.K2461()
sb.connect(8)
pg.connect()
probe_current = 100e-6

ass1 = {"I+": "A", "I-": "D", "V1+": "B", "V1-": "C"}
ass2 = {"I+": "D", "I-": "G", "V1+": "E", "V1-": "F"}
ass3 = {"I+": "A", "I-": "D", "V1+": "B", "V1-": "C"}
ass4 = {"I+": "A", "I-": "D", "V1+": "B", "V1-": "C"}
ass5 = {"I+": "A", "I-": "D", "V1+": "B", "V1-": "C"}
ass6 = {"I+": "A", "I-": "D", "V1+": "B", "V1-": "C"}
ass7 = {"I+": "A", "I-": "D", "V1+": "B", "V1-": "C"}
ass8 = {"I+": "A", "I-": "D", "V1+": "B", "V1-": "C"}

R = [0, 0, 0, 0, 0, 0, 0, 0]

sb.switch(ass1)
time.sleep(0.2)
pg.enable_4_wire_probe(probe_current)
time.sleep(0.2)
c, v = pg.read_one()
R[0] = v / c
pg.disable_probe_current()
time.sleep(0.2)

sb.switch(ass2)
time.sleep(0.2)
pg.enable_4_wire_probe(probe_current)
time.sleep(0.2)
c, v = pg.read_one()
R[1] = v / c
pg.disable_probe_current()
time.sleep(0.2)

sb.switch(ass3)
time.sleep(0.2)
pg.enable_4_wire_probe(probe_current)
time.sleep(0.2)
c, v = pg.read_one()
R[2] = v / c
pg.disable_probe_current()
time.sleep(0.2)

sb.switch(ass4)
time.sleep(0.2)
pg.enable_4_wire_probe(probe_current)
time.sleep(0.2)
c, v = pg.read_one()
R[3] = v / c
pg.disable_probe_current()
time.sleep(0.2)

sb.switch(ass5)
time.sleep(0.2)
pg.enable_4_wire_probe(probe_current)
time.sleep(0.2)
c, v = pg.read_one()
R[4] = v / c
pg.disable_probe_current()
time.sleep(0.2)

sb.switch(ass6)
time.sleep(0.2)
pg.enable_4_wire_probe(probe_current)
time.sleep(0.2)
c, v = pg.read_one()
R[5] = v / c
pg.disable_probe_current()
time.sleep(0.2)

sb.switch(ass7)
time.sleep(0.2)
pg.enable_4_wire_probe(probe_current)
time.sleep(0.2)
c, v = pg.read_one()
R[6] = v / c
pg.disable_probe_current()
time.sleep(0.2)

sb.switch(ass8)
time.sleep(0.2)
pg.enable_4_wire_probe(probe_current)
time.sleep(0.2)
c, v = pg.read_one()
R[7] = v / c
pg.disable_probe_current()
time.sleep(0.2)


print('Resistances: \n', R)
pg.disable_probe_current()
R = np.array(R)
name = dialog.asksaveasfilename(title='Save')
if name:  # if a name was entered, don't save otherwise
    if name[-4:] != '.txt':  # add .txt if not already there
        name = f'{name}.txt'
    np.savetxt(name, R, newline='\r\n', delimiter='\t')  # save
    print(f'Data saved as {name}')
else:
    print('Data not saved')

