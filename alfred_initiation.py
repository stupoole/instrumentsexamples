import time
import instruments
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from tkinter import filedialog as dialog

matplotlib.use('Qt5Agg')


def save(data, header):
    name = dialog.asksaveasfilename(title='Save data')
    if name:  # if a name was entered, don't save otherwise
        if name[-4:] != '.txt':  # add .txt if not already there
            name = f'{name}.txt'
        np.savetxt(name, data, header=header, newline='\n', delimiter='\t')  # save
        print(f'Data saved as {name}')
    else:
        print('Data not saved')


numpoints = 10
RxxData = np.zeros(numpoints)
RxyData = np.zeros(numpoints)
TimeData = np.zeros(numpoints)
pg = instruments.K2400()
dmm = instruments.K2000()
sb = instruments.SwitchBox()

dmm.connect(6)
pg.connect(9)
sb.connect(15)

measure_assignment = {"I+": "A", "I-": "E", "V2+": "C", "V2-": "G",  "V1+":"B", "V1-":"D"}
pg.prepare_measure_one(100e-6, four_wire=False)
sb.switch(measure_assignment)
time.sleep(0.5)
pg.enable_output_current()
dmm.prepare_measure_one(0, 2)
start_time = time.time()
for m in range(numpoints):
    time.sleep(0.1)
    t, voltage, current = pg.read_one()
    volt2 = dmm.read_one()
    RxxData[m] = voltage / current
    RxyData[m] = volt2 / current
    TimeData[m] = time.time() - start_time
pg.disable_output_current()
time.sleep(0.5)
sb.close()
dmm.close()
pg.close()
figure = plt.figure(1)
figure.canvas.set_window_title('Resistance Plots')
ax = figure.add_subplot(111)
ax.plot(TimeData, RxxData)
plt.xlabel('Time(s)')
plt.ylabel('Resistance (Ohms)')
ax.grid()
ax.ticklabel_format(useOffset=False)


data = np.column_stack((TimeData, RxxData, RxyData))
save(data, 't (s), Rxx (Ohms), Rxy (Ohms)')
plt.show()
