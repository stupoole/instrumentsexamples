import instruments

import numpy as np
import matplotlib.pyplot as plt
import time

import tkinter as tk
import tkinter.messagebox as mb
from tkinter import filedialog as dialog

num = 100
current = 2
frequency = 1000
pulse1_assignments = {"I+": "AG", "I-": "CE"}  # configuration for a pulse from B to F
pulse2_assignments = {"I+": "AC", "I-": "GE"}  # configuration for a pulse from D to H
# measure_assignments = {"I+": "A", "I-": "E", "V1+": "A", "V1-": "E", "V2+": "C", "V2-": "G"}
measure_assignments = {"I+": "C", "I-": "G", "V1+": "C", "V1-": "G", "V2+": "E", "V2-": "A"}

top_lockin = instruments.SR830_RS232()
bot_lockin = instruments.SR830_RS232()
source = instruments.K6221()
sb = instruments.SwitchBox()
# pg = instruments.K2461()


sb.connect(15)
source.connect_RS232(16)
top_lockin.connect(6)
bot_lockin.connect(10)
# pg.connect()
sb.switch(measure_assignments)


source.sine_wave(frequency, current)
source.set_phase_marker()
source.wave_output_on()

time.sleep(2)

top_lockin.set_harmonic(1)
top_lockin.set_time_constant(0.1)
top_lockin.auto_phase()
top_lockin.set_harmonic(2)
top_lockin.auto_range()
top_lockin.set_filter(12)

bot_lockin.set_harmonic(1)
bot_lockin.set_time_constant(0.1)
bot_lockin.auto_phase()
bot_lockin.set_harmonic(2)
bot_lockin.auto_range()
bot_lockin.set_filter(12)

t = np.empty(num)

rxx_r = np.empty(num)
rxx_theta = np.empty(num)

rxy_r = np.empty(num)
rxy_theta = np.empty(num)

fig = plt.figure(1)
rxx_ax = plt.subplot(211)
rxy_ax = plt.subplot(212)


rxx_pos_line, = rxx_ax.plot(t, rxx_r, 'k.')
rxx_ax.set_ylabel('R_xx (Ohms)')
rxx_ax.ticklabel_format(useOffset=False)

rxy_pos_line, = rxy_ax.plot(t, rxy_r, 'k.')
rxy_ax.set_ylabel('R_xy (Ohms)')
rxy_ax.set_xlabel('Time (s)')
rxy_ax.ticklabel_format(useOffset=False)
# plt.show(block=False)
plt.pause(0.001)
time.sleep(10)

start_time = time.time()
for i in range(0, num):
    t[i] = time.time() - start_time
    rxx_r[i] = top_lockin.get_radius()
    rxx_theta[i] = top_lockin.get_angle()
    rxy_r[i] = bot_lockin.get_radius()
    rxy_theta[i] = bot_lockin.get_angle()
    rxx_pos_line.set_data(t, rxx_r/(current*1e-3))
    rxy_pos_line.set_data(t, rxy_r/(current*1e-3))
    rxx_ax.relim()
    rxx_ax.autoscale_view()
    rxy_ax.relim()
    rxy_ax.autoscale_view()

    plt.pause(0.01)

source.wave_output_off()
source.close()
sb.reset_all()

root = tk.Tk()
root.withdraw()
data = np.column_stack((t, rxx_r, rxx_theta, rxy_r, rxy_theta))
name = dialog.asksaveasfilename(title='Save')
if name:  # if a name was entered, don't save otherwise
    if name[-4:] != '.txt':  # add .txt if not already there
        name = f'{name}.txt'
    np.savetxt(name, data, newline='\r\n', delimiter='\t')  # save
    print(f'Data saved as {name}')
else:
    print('Data not saved')

plt.show()
