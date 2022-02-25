import instruments

import numpy as np
import matplotlib.pyplot as plt
import time
import pandas as pd

import tkinter as tk
import tkinter.messagebox as mb
from tkinter import filedialog as dialog


def ass_to_str(assignment):
    ass_string = str(assignment.values()).strip()
    string = ",".join(x for x in ass_string if x.isalpha()).replace('d,i,c,t,v,a,l,u,e,s,', '').upper()
    if string.strip()=="":
        string = ",".join(x for x in ass_string if x.isnumeric())
    return string

I_pulse = 35e-3  # step this one up in medium steps up to 20 then tiny steps up to 30 onwards
probe_duration = 360  # number of seconds to measure for

delay = 100e-3
loop_number = 3
I_probe = 13e-3  # keep constant
pre_repeats = int(probe_duration / (2 * delay))
post_repeats = int(probe_duration / (2 * delay))
channel = 1
volt_range = 100e-3
width = 500e-6
compliance = 40
bias = 0.0

probe_assignments = [{"I+": "A", "I-": "E", "V2+": "C", "V2-": "G"},
                     {"I+": "E", "I-": "A", "V2+": "C", "V2-": "G"},
                     {"I+": "B", "I-": "F", "V2+": "D", "V2-": "H"},
                     {"I+": "F", "I-": "B", "V2+": "D", "V2-": "H"},
                     {"I+": "C", "I-": "G", "V2+": "E", "V2-": "A"},
                     {"I+": "G", "I-": "C", "V2+": "E", "V2-": "A"},
                     {"I+": "D", "I-": "H", "V2+": "F", "V2-": "B"},
                     {"I+": "H", "I-": "D", "V2+": "F", "V2-": "B"}]

pulse_assignments = [{"I+": "D", "I-": "H", "V2+": "F", "V2-": "B"},
                     {"I+": "F", "I-": "B", "V2+": "H", "V2-": "D"}]

curr_list = np.array([I_probe, -I_probe])
curr_vals_pre_probe = np.tile(curr_list, pre_repeats)
curr_vals_post_probe = np.tile(curr_list, post_repeats)

pulse_current_data = []
pulse_voltage_data = []
pulse_time_data = []
pulse_assignment_data = []
probe_assignment_data = []
final_dataframe = pd.DataFrame()

source = instruments.K6221()
sb = instruments.SwitchBox()

sb.connect(3)
source.connect_ethernet()

absolute_reference_time = time.time()

source.set_compliance(compliance)
source.set_sense_chan_and_range(channel, volt_range)
source.configure_custom_sweep(curr_list, delay, compliance, pre_repeats, bias, 'best')
source.configure_pulse(width, 1, 1)
sb.switch(probe_assignments[0])
print('Arming pre_pulse  probing')
source.arm_pulse_sweep()
time.sleep(1)

pre_start_time = time.time()
print('Starting probing')
source.trigger()
time.sleep(5)
pulse_data = source.get_trace(delay=5)
print('Data retrieved')
pre_voltage_data = pulse_data[0::2]
pre_time_data = pulse_data[1::2]
fig = plt.figure()
delta_ax = fig.add_subplot(211)
# plt.xlabel('Time(s)')
plt.ylabel('Delta Voltage (Volts)')
res_ax = fig.add_subplot(212)
plt.xlabel('Time(s)')
plt.ylabel('Rxy (Ohms)')
pre_delta_line, = delta_ax.plot((pre_start_time - absolute_reference_time + pre_time_data)[0::2],
                                pre_voltage_data[0::2] + pre_voltage_data[1::2], 'g+')
pre_res_line, = res_ax.plot(pre_start_time - absolute_reference_time + pre_time_data,
                            np.abs(pre_voltage_data / curr_vals_pre_probe), 'g+')
# pulse_line, = ax.plot([], [], 'r+')
probe_delta_line, = delta_ax.plot([], [], 'k+')
probe_res_line, = res_ax.plot([], [], 'k+')

pre_dataframe = pd.DataFrame({'I+': curr_vals_pre_probe[0::2], 'V+': pre_voltage_data[0::2], 't+': pre_time_data[0::2],
                              'I-': curr_vals_pre_probe[1::2], 'V-': pre_voltage_data[1::2], 't-': pre_time_data[1::2],
                              'type': 'pre', 'probe': ass_to_str(probe_assignments[0])})

final_dataframe = final_dataframe.append(pre_dataframe)

for loop_count in range(loop_number):
    for probe_assignment_count, probe_assignment in enumerate(probe_assignments):
        for pulse_assignment_count, pulse_assignment in enumerate(pulse_assignments):
            print(f'Switching to {ass_to_str(pulse_assignment)}')
            sb.switch(pulse_assignment)
            source.configure_custom_sweep([I_pulse], delay, compliance, 1, bias, 'best')
            source.configure_pulse(width, 1, 1)
            time.sleep(1)
            print('Arming switching pulse')
            source.arm_pulse_sweep()
            print('Sending pulse')
            pulse_time = time.time() - absolute_reference_time
            source.trigger()
            time.sleep(0.5)
            data = source.get_trace(delay=0.1)
            print('Data retrieved')
            pulse_voltage = data[0::2][0]
            pulse_voltage_data.append(pulse_voltage)
            pulse_time_data.append(pulse_time)
            pulse_current_data.append(I_pulse)
            pulse_assignment_data.append(ass_to_str(pulse_assignment))
            probe_assignment_data.append(ass_to_str(probe_assignment))

            sb.switch(probe_assignment)
            source.configure_custom_sweep(curr_list, delay, compliance, post_repeats, bias, 'best')
            source.configure_pulse(width, 1, 1)
            time.sleep(0.5)
            print('Arming probe pulses')
            source.arm_pulse_sweep()
            print('Starting probing')
            probe_time = time.time() - absolute_reference_time
            source.trigger()
            data = source.get_trace(delay=1)
            print('Data retrieved')
            print('Time taken: ', time.time() - absolute_reference_time - probe_time)
            voltage = data[0::2]
            time_data = data[1::2] + probe_time

            final_dataframe = final_dataframe.append(pd.DataFrame(
                {'I+': curr_vals_post_probe[0::2], 'I-': curr_vals_post_probe[1::2], 'V+': voltage[0::2],
                 'V-': voltage[1::2], 't+': time_data[0::2], 't-': time_data[1::2],
                 'pump': ass_to_str(pulse_assignment), 'probe': ass_to_str(probe_assignment), 'type': 'measurement',
                 'loop': loop_count}))
            full_data = final_dataframe.loc[final_dataframe['type'] == 'measurement']
            tdata = full_data['t+'].append(full_data['t-']).to_numpy()
            vdata = full_data['V+'].append(full_data['V-']).to_numpy()
            idata = full_data['I+'].append(full_data['I-']).to_numpy()
            probe_delta_line.set_xdata(tdata[0::2])
            probe_delta_line.set_ydata(vdata[0::2] + vdata[1::2])

            probe_res_line.set_xdata(tdata)
            probe_res_line.set_ydata(np.abs(vdata / idata))

            delta_ax.relim()
            delta_ax.autoscale_view()

            res_ax.relim()
            res_ax.autoscale_view()

            fig.canvas.draw()
            fig.canvas.flush_events()

            plt.pause(0.1)
    pulse_df = pd.DataFrame(
        {'I+': pulse_current_data, 'V+': pulse_voltage_data, 't+': pulse_time_data, 'pump': pulse_assignment_data,
         'type': 'pulse', 'loop': loop_count})
    final_dataframe = final_dataframe.append(pulse_df)
    final_dataframe.to_hdf('temp_dataframe.hdf', key='data', mode='w')
    print('Saving temp data as: temp_dataframe.hdf')

source.close()
sb.close()
meta_df = pd.DataFrame(
    data={'probe_duration': [probe_duration], 'delay': delay, 'loop_number': loop_number,
          'pre_repeats': pre_repeats, 'post_repeats': post_repeats, 'channel': channel,
          'volt_range': volt_range, 'width': width, 'compliance': compliance, 'bias': bias,
          'absolute_reference_time': absolute_reference_time})

name = dialog.asksaveasfilename(title='Save')
name = name.replace('.txt', '')
name = name.replace('.hdf', '')
name = name.replace('.h5', '')
name += '.h5'
if name:  # if a name was entered, don't save otherwise
    store = pd.HDFStore(name)
    store['meta_data'] = meta_df
    store['data'] = final_dataframe
    print(f'Data saved as {name}')
    store.close()
else:
    print('Data not saved')
