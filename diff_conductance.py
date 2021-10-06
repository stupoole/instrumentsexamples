import Instruments

import numpy as np
import matplotlib.pyplot as plt
import time

import tkinter as tk
import tkinter.messagebox as mb
from tkinter import filedialog as dialog

frequency = 1
start = -8e-3
stop = 8e-3
step = 0.1e-3
delta = 0.1e-3
delay = 2e-3
repeats = 5
channel = 1
volt_range = 1
loop_delay = 10

current = np.tile(np.linspace(start, stop, round((stop - start) / step) + 1), repeats)

source = Instruments.K6221()
source.connect_ethernet()
source.set_compliance(40)
source.set_sense_chan_and_range(channel, volt_range)
source.configure_diff_conductance(start, stop, step, delta, delay)

time.sleep(2)


t = np.array([])
dv = np.array([])
start_time = time.time()
for i in range(repeats):
    source.arm_diff_cond()
    time.sleep(loop_delay)
    source.trigger()

    time.sleep(1)
    data = source.get_trace(12)
    dv_temp = data[0::2]
    t_temp = data[1::2]
    t = np.append(t, t_temp)
    dv = np.append(dv, dv_temp)


print('time taken: ', time.time()-start_time)
my_scatter, = plt.plot(current[0:len(dv)], dv, 'k.')

plt.ticklabel_format(useOffset=False)
plt.xlabel('Current (mA)')
plt.ylabel('Voltage (V)')

plt.pause(1)

save_data = np.column_stack((current[0:len(dv)], dv, t))
print(len(current), len(dv))

name = dialog.asksaveasfilename(title='Save')
if name:  # if a name was entered, don't save otherwise
    if name[-4:] != '.txt':  # add .txt if not already there
        name = f'{name}.txt'
    np.savetxt(name, save_data, newline='\n', delimiter='\t')  # save
    print(f'Data saved as {name}')
else:
    print('Data not saved')

plt.show()
