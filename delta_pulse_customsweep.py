import Instruments

import numpy as np
import matplotlib.pyplot as plt
import time

import tkinter as tk
import tkinter.messagebox as mb
from tkinter import filedialog as dialog

frequency = 1

I_max = 15e-3  # Used 15mA to RC124 10um, 10mA for RC123 10um UJ, 5mA for RC123 5um UJ
step = 0.25e-3  # Used 0.1mA steps for 5um RC123 UJ otherwise 0.25mA
delay = 1
repeats = 20
channel = 1
volt_range = 100e-3  # 10 for Rxx # 100e-3 for Rxy sweep 1
width = 500e-6
compliance = 40
bias = 0.0

curr_list = np.concatenate((np.linspace(0, I_max, round(I_max / step) + 1),
                            np.linspace(I_max - step, -I_max, round(2 * I_max / step)),
                            np.linspace(-I_max + step, 0, round(I_max / step))))

source = Instruments.K6221()
source.connect_ethernet()
source.set_compliance(60)
source.set_sense_chan_and_range(channel, volt_range)
source.configure_custom_sweep(curr_list[1::], delay, compliance, repeats, bias, 'best')
source.configure_pulse(width, 1, 1)

source.arm_pulse_sweep()
time.sleep(2)
source.trigger()
start_time = time.time()
time.sleep(5)
data = source.get_trace()
# time.sleep(2)
# source.close()

print('time taken: ', time.time() - start_time)
voltage = data[0::2]

curr_vals = np.tile(curr_list, repeats)
my_scatter, = plt.plot(curr_vals[0:len(voltage)], voltage, 'k.')

my_line, = plt.plot([min(curr_vals), max(curr_vals)], [min(voltage), max(voltage)], 'r-')
plt.ticklabel_format(useOffset=False)
plt.xlabel('Current (mA)')
plt.ylabel('Voltage (V)')

plt.pause(1)


save_data = np.column_stack((curr_vals[0:len(voltage)], voltage))
print(len(curr_vals), len(voltage))

name = dialog.asksaveasfilename(title='Save')
if name:  # if a name was entered, don't save otherwise
    if name[-4:] != '.txt':  # add .txt if not already there
        name = f'{name}.txt'
    np.savetxt(name, save_data, newline='\n', delimiter='\t')  # save
    print(f'Data saved as {name}')
else:
    print('Data not saved')

plt.show()
