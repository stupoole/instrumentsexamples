import instruments

import numpy as np
import matplotlib.pyplot as plt
import time

import tkinter as tk
import tkinter.messagebox as mb
from tkinter import filedialog as dialog

frequency = 1
start = -17e-3
stop = 17e-3
step = 0.1e-3
delay = 1
repeats = 20
channel = 2
volt_range = 100e-3
width = 500e-6

current = np.tile(np.linspace(start, stop, round((stop - start) / step) + 1), repeats)
source = instruments.K6221()
source.connect_ethernet()
source.set_compliance(40)
source.set_sense_chan_and_range(channel, volt_range)
source.configure_linear_sweep(start, stop, step, delay, repeats)
source.configure_pulse(width, 1, 1)

source.arm_pulse_sweep()
time.sleep(2)
source.trigger()
start_time = time.time()
time.sleep(5)
data = source.get_trace()
print('time taken: ', time.time()-start_time)
voltage = data[0::2]

my_scatter, = plt.plot(current[0:len(voltage)], voltage, 'k.')

my_line, = plt.plot([min(current), max(current)], [min(voltage), max(voltage)], 'r-')
plt.ticklabel_format(useOffset=False)
plt.xlabel('Current (mA)')
plt.ylabel('Voltage (V)')

plt.pause(1)

save_data = np.column_stack((current[0:len(voltage)], voltage))
print(len(current), len(voltage))

name = dialog.asksaveasfilename(title='Save')
if name:  # if a name was entered, don't save otherwise
    if name[-4:] != '.txt':  # add .txt if not already there
        name = f'{name}.txt'
    np.savetxt(name, save_data, newline='\n', delimiter='\t')  # save
    print(f'Data saved as {name}')
else:
    print('Data not saved')

plt.show()
