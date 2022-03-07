import instruments
import pandas as pd

import numpy as np
import matplotlib.pyplot as plt
import time

import tkinter as tk
import tkinter.messagebox as mb
from tkinter import filedialog as dialog


def ass_to_str(assignment):
    ass_string = str(assignment.values()).strip()
    string = ",".join(x for x in ass_string if x.isalpha()).replace('d,i,c,t,v,a,l,u,e,s,', '').upper()
    if string.strip() == "":
        string = ",".join(x for x in ass_string if x.isnumeric())
    return string


frequency = 1

I_max = 15e-3  # Used 15mA to RC124 10um, 10mA for RC123 10um UJ, 5mA for RC123 5um UJ
step = 1e-3  # Used 0.1mA steps for 5um RC123 UJ otherwise 0.25mA
delay = 1
repeats = 3
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

final_dataframe = pd.DataFrame()

source = instruments.K6221()
sb = instruments.SwitchBox()
sb.connect(12)
source.connect_ethernet()

absolute_reference_time = time.time()

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
    probe_time = time.time()
    time.sleep(5)
    # get_trace() loops until data is ready or it crashes.
    data = source.get_trace()
    print('Data retrieved')

    print('Time taken: ', time.time() - probe_time)
    voltage_data = data[0::2]
    current_data = curr_vals[0:len(voltage_data)]
    time_data = data[1::2] + probe_time
    plt.plot(current_data, voltage_data, plot_styles[i])

    plt.ticklabel_format(useOffset=False)
    plt.xlabel('Current (mA)')
    plt.ylabel('Voltage (V)')

    temp_df = pd.DataFrame(
        {'I': current_data, 'V': voltage_data, 't': time_data, 'probe': ass_to_str(assignment),
         'type': 'probe', 'assignment_index': i})
    final_dataframe = final_dataframe.append(temp_df)
    final_dataframe.to_hdf('temp_dataframe.h5', key='data', mode='w')
    print('Saving temp data as: temp_dataframe.h5')


time_taken = time.time() - absolute_reference_time
meta_df = pd.DataFrame(
    data={'delay': delay, 'repeats': repeats, 'channel': channel, 'volt_range': volt_range, 'width': width,
          'compliance': compliance, 'bias': bias, 'absolute_reference_time': absolute_reference_time,
          'time_taken': time_taken, 'max_current': I_max, 'I_step': step, 'current_values': [curr_list]})

name = dialog.asksaveasfilename(title='Save')
name = name.replace('.txt', '')
name = name.replace('.hdf', '')
name = name.replace('.h5', '')
name = name.replace('.hd5', '')
name += '.h5'
if name:  # if a name was entered, don't save otherwise
    store = pd.HDFStore(name)
    store['meta_data'] = meta_df
    store['data'] = final_dataframe
    print(f'Data saved as {name}')
    store.close()
else:
    print('Data not saved')

plt.show()

time.sleep(2)
source.close()
sb.close()
