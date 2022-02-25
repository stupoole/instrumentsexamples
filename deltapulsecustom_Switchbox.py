import instruments

import numpy as np
import matplotlib.pyplot as plt
import time

import tkinter as tk
import tkinter.messagebox as mb
from tkinter import filedialog as dialog


def save(name, save_data, header):
    print(save_data.shape)
    if name:  # if a name was entered, don't save otherwise
        if name[-4:] != '.txt':  # add .txt if not already there
            name = f'{name}.txt'
        np.savetxt(name, save_data, header=header, newline='\r\n', delimiter='\t')  # save
        print(f'Data saved as {name}')
    else:
        print('Data not saved')


frequency = 1

I_max = 10e-3  # Used 15mA to RC124 10um, 10mA for RC123 10um UJ, 5mA for RC123 5um UJ
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
curr_vals = np.tile(curr_list, repeats)

assignments = [{"I+": "A", "I-": "E", "V2+": "C", "V2-": "G"},
               {"I+": "E", "I-": "A", "V2+": "C", "V2-": "G"},
               {"I+": "B", "I-": "F", "V2+": "D", "V2-": "H"},
               {"I+": "F", "I-": "B", "V2+": "D", "V2-": "H"},
               {"I+": "C", "I-": "G", "V2+": "E", "V2-": "A"},
               {"I+": "G", "I-": "C", "V2+": "E", "V2-": "A"},
               {"I+": "D", "I-": "H", "V2+": "F", "V2-": "B"},
               {"I+": "H", "I-": "D", "V2+": "F", "V2-": "B"}]

plot_styles = ['k.', 'k.', 'b+', 'b+', 'ro', 'ro', 'g*', 'g*']
datasets = []
header = ""

source = instruments.K6221()
sb = instruments.SwitchBox()
sb.connect(3)

source.connect_ethernet()
source.set_compliance(compliance)
source.set_sense_chan_and_range(channel, volt_range)
source.configure_custom_sweep(curr_list[1::], delay, compliance, repeats, bias, 'best')
source.configure_pulse(width, 1, 1)

for i, assignment in enumerate(assignments):
    print(f'Switching to {assignment}')
    sb.switch(assignment)
    time.sleep(1)
    print('Arming pulse')
    source.arm_pulse_sweep()
    time.sleep(2)
    print('Starting measurement')
    source.trigger()
    start_time = time.time()
    time.sleep(5)
    # get_trace() loops until data is ready or it crashes.
    data = source.get_trace()
    print('Data retrieved')

    print('Time taken: ', time.time() - start_time)
    voltage = data[0::2]
    plt.plot(curr_vals[0:len(voltage)], voltage, plot_styles[i])

    plt.ticklabel_format(useOffset=False)
    plt.xlabel('Current (mA)')
    plt.ylabel('Voltage (V)')

    datasets.append(np.column_stack((curr_vals[0:len(voltage)], voltage)))

    ass_string = str(assignment.values()).strip()
    header += ''.join(x for x in ass_string if x.isalpha())[-4:] + ", "

    temp_data = np.column_stack(datasets)

    save("temp_data.txt", temp_data, header)

file_name = dialog.asksaveasfilename(title='Save')
save(file_name, np.column_stack(datasets), header)
plt.show()

time.sleep(2)
source.close()
sb.close()
