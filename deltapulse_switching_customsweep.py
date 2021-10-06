import Instruments

import numpy as np
import matplotlib.pyplot as plt
import time

import tkinter as tk
import tkinter.messagebox as mb
from tkinter import filedialog as dialog

frequency = 1

I_pulse = 50e-3  # Used 17mA for 5um LXB025 UJ.
I_probe = 10e-3
pulse_delay = 30
probe_delay = 1
probe_count = 20

repeats = 5
channel = 1
volt_range = 100e-3  # 10 for Rxx # 100e-3 for Rxy sweep 1
width = 500e-6
compliance = 105

curr_list = np.array([I_pulse] + probe_count*[I_probe, -I_probe] + [-I_pulse] + probe_count*[I_probe, -I_probe])
delay_list = np.array([pulse_delay] + 2*probe_count*[probe_delay] + [pulse_delay] + 2*probe_count*[probe_delay])

source = Instruments.K6221()
source.connect_ethernet()
source.set_compliance(compliance)
source.set_sense_chan_and_range(channel, volt_range)
source.configure_switching_custom_sweep(curr_list, delay_list, compliance, repeats)
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
time_data = data[1::2]
voltage = data[0::2]

curr_vals = np.tile(curr_list, repeats)
my_scatter, = plt.plot(curr_vals[0:len(voltage)], voltage, 'k.')

my_line, = plt.plot([min(curr_vals), max(curr_vals)], [min(voltage), max(voltage)], 'r-')
plt.ticklabel_format(useOffset=False)
plt.xlabel('Current (mA)')
plt.ylabel('Voltage (V)')

plt.pause(1)

plt.figure()
plt.plot(time_data, voltage, 'k.')

plt.ticklabel_format(useOffset=False)
plt.xlabel('Time (s)')
plt.ylabel('Voltage (V)')

plt.pause(1)

save_data = np.column_stack((curr_vals[0:len(voltage)], voltage, time_data))
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
