import Instruments
import time
import numpy as np
from tkinter import filedialog as dialog

sb = Instruments.SwitchBox()
pg = Instruments.K2400()
bb = Instruments.BalanceBox()

assignments_0 = {"I+": "A", "I-": "E", "V1+": "B", "V1-": "D"}
assignments_1 = {"I+": "A", "I-": "E", "V1+": "H", "V1-": "F"}
assignments_2 = {"I+": "C", "I-": "G", "V1+": "D", "V1-": "F"}
assignments_3 = {"I+": "C", "I-": "G", "V1+": "B", "V1-": "H"}

assignments = [assignments_0, assignments_1, assignments_2, assignments_3]
pg.connect(6)
sb.connect(8)
bb.connect(7)

bb.enable_all()
bb.reset_resistances()
data = np.zeros((25, 5))

for ass in range(4):
    sb.switch(assignments[ass])
    time.sleep(200e-3)
    for i in range(1, 50, 2):
        current = i * 1e-6
        pg.prepare_measure_n(current, 10)
        time.sleep(100e-3)
        pg.trigger()
        time.sleep(3)
        t, c, v = pg.read_buffer()
        print(f"current: {current}, Rxy: ", sum(v / c) / 10)
        data[int(i / 2), 0] = current
        data[int(i / 2), ass + 1] = sum(v) / 10

pg.close()
sb.reset_all()
sb.close()
bb.disable_all()
bb.close()

name = dialog.asksaveasfilename(title='Save')
if name:  # if a name was entered, don't save otherwise
    if name[-4:] != '.txt':  # add .txt if not already there
        name = f'{name}.txt'
    np.savetxt(name, data, newline='\r\n', delimiter='\t')  # save
    print(f'Data saved as {name}')
else:
    print('Data not saved')
