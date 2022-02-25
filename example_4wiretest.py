import instruments
import time
import numpy as np
from tkinter import filedialog as dialog

sb = instruments.SwitchBox()
pg = instruments.K2461()
sb.connect(7)
pg.connect()
probe_current = 100e-6

ass1 = {"I+": "A", "I-": "E", "V1+": "B", "V1-": "D"}
ass2 = {"I+": "B", "I-": "F", "V1+": "C", "V1-": "E"}
ass3 = {"I+": "C", "I-": "G", "V1+": "D", "V1-": "F"}
ass4 = {"I+": "D", "I-": "H", "V1+": "E", "V1-": "G"}


R = [0, 0, 0, 0]

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

pg.close()
sb.close()

print('Resistances: \n', R)
R = np.array(R)
name = dialog.asksaveasfilename(title='Save')
if name:  # if a name was entered, don't save otherwise
    if name[-4:] != '.txt':  # add .txt if not already there
        name = f'{name}.txt'
    np.savetxt(name, R, newline='\n', delimiter='\t')  # save
    print(f'Data saved as {name}')
else:
    print('Data not saved')

