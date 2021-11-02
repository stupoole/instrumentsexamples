import numpy as np
import time
import matplotlib
import instruments
import winsound
import tkinter as tk
from tkinter import filedialog as dialog

matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt

def error_sound():
    winsound.Beep(880, 200)
    winsound.Beep(440, 200)


def alert_sound():
    winsound.Beep(440, 200)
    winsound.Beep(660, 200)
    winsound.Beep(880, 200)


pulse1_assignments = {"I+": "B", "I-": "F"}  # configuration for a pulse from B to F
pulse2_assignments = {"I+": "D", "I-": "H"}  # configuration for a pulse from D to H
measure_assignments = {"V2+": "C", "V2-": "G", "V1+": "B", "V1-": "D", "I+": "A", "I-": "E"}

# Parameters to be changed
pulse_current = 24.8e-3  # set current
# pulse_voltage = 30  # set voltage
pulse_width = 1e-3  # set pulse duration
measure_current = 100e-6  # measurement current
measure_number = 300  # number of measurements to store in buffer when calling measure_n and read_buffer. 375 is ~1min
num_loops = 3
measure_delay = measure_number * 0.15  # Not strictly necessary.
pulse_interval = 5  # Pause between pulses in minutes.

pos_time = np.array([])
neg_time = np.array([])
pos_rxx = np.array([])
neg_rxx = np.array([])
pos_rxy = np.array([])
neg_rxy = np.array([])

switch_box = instruments.SwitchBox()  # make a sb object
pulse_generator = instruments.K2461()  # make a k2461 object
keithley = instruments.K2000()  # make a k2000 object
start_time = time.time()  # use this for the graphing only

# actually connect to the instruments
pulse_generator.connect(timeout=320000)
switch_box.connect(3)
keithley.connect(6, timeout=320000)

plt.figure(1)
plt.xlabel('Time (s)')
plt.ylabel('R_xx (Ohms)')
plt.ticklabel_format(useOffset=False)
plt.figure(2)
plt.xlabel('Time (s)')
plt.ylabel('R_xy (Ohms)')
plt.ticklabel_format(useOffset=False)

for i in range(num_loops):
    #-------PULSE 1--------#
    pulse1_start_time = time.time()
    switch_box.switch(measure_assignments)
    pulse_generator.measure_n(measure_current, 10, nplc=10)
    keithley.prepare_measure_n(10, nplc=10)
    plt.pause(500e-3)
    prepulse1_time = time.time()
    keithley.trigger()  # actually starts measuring
    pulse_generator.trigger()  # actually starts the measuring
    t, vxx, curr = pulse_generator.read_buffer(10)
    vxy = keithley.read_buffer()
    pos_time = np.append(pos_time, t)
    pos_rxx = np.append(pos_rxx, vxx/curr)
    pos_rxy = np.append(pos_rxy, vxy/curr)

    # pulse in one direction
    switch_box.switch(pulse1_assignments)
    plt.pause(500e-3)  # pauses to allow changes to apply before telling them to do something else.
    pulse1_time = time.time()
    pulse_generator.prepare_pulsing_current(pulse_current, pulse_width, vlim=100)  # sends a pulse with given params
    pulse_generator.send_pulse()
    # print('Pulse current: ', pulse_current)  # just to show the set value.
    plt.pause(500e-3)
    switch_box.switch(measure_assignments)
    pulse_generator.measure_n(measure_current, measure_number, nplc=10)
    keithley.prepare_measure_n(measure_number, nplc=10)
    plt.pause(500e-3)
    keithley.trigger()  # actually starts measuring
    pulse_generator.trigger()  # actually starts the measuring
    t, vxx, curr = pulse_generator.read_buffer(measure_number)
    vxy = keithley.read_buffer()
    pos_time = np.append(pos_time, t + pulse1_time - pulse1_start_time)
    pos_rxx = np.append(pos_rxx, vxx / curr)
    pos_rxy = np.append(pos_rxy, vxy / curr)

    plt.figure(1)
    plt.plot(pos_time, pos_rxx, 'k+')
    plt.draw()
    plt.figure(2)
    plt.plot(pos_time, pos_rxy, 'k+')
    plt.draw()

    plt.pause(pulse_interval*60)

    #--------------PULSE 2---------------#
    pulse2_start_time = time.time()
    switch_box.switch(measure_assignments)
    pulse_generator.measure_n(measure_current, 10, nplc=10)
    keithley.prepare_measure_n(10, nplc=10)
    plt.pause(500e-3)
    prepulse2_time = time.time()
    keithley.trigger()  # actually starts measuring
    pulse_generator.trigger()  # actually starts the measuring
    t, vxx, curr = pulse_generator.read_buffer(10)
    vxy = keithley.read_buffer()
    neg_time = np.append(neg_time, t)  # Needs looking at.
    neg_rxx = np.append(neg_rxx, vxx / curr)
    neg_rxy = np.append(neg_rxy, vxy / curr)

    # repeat of above with other pulse direction.
    switch_box.switch(pulse2_assignments)
    plt.pause(500e-3)
    pulse2_time = time.time()
    pulse_generator.prepare_pulsing_current(pulse_current, pulse_width, vlim=100)
    pulse_generator.send_pulse()
    plt.pause(500e-3)
    switch_box.switch(measure_assignments)
    pulse_generator.measure_n(measure_current, measure_number, nplc=10)
    keithley.prepare_measure_n(measure_number, nplc=10)
    plt.pause(500e-3)
    keithley.trigger()  # actually starts measuring
    pulse_generator.trigger()  # actually starts the measuring
    t, vxx, curr = pulse_generator.read_buffer(measure_number)
    vxy = keithley.read_buffer()
    neg_time = np.append(neg_time, t + pulse2_time - pulse2_start_time)  # Needs looking at.
    neg_rxx = np.append(neg_rxx, vxx / curr)
    neg_rxy = np.append(neg_rxy, vxy / curr)

    plt.figure(1)
    plt.plot(neg_time, neg_rxx, 'r+')
    plt.draw()
    plt.figure(2)
    plt.plot(neg_time, neg_rxy, 'r+')
    plt.draw()

    plt.pause(pulse_interval * 60)
    print(i)

switch_box.reset_all()
alert_sound()

data = np.column_stack((pos_time, pos_rxx, pos_rxy, neg_time, neg_rxx, neg_rxy))
header = f"pos_time, pos_rxx, pos_rxy, neg_time, neg_rxx, neg_rxy, n_pre_pulse:{10}, n_measure:{measure_number}, n_loops:{num_loops}, meas_curr:{measure_current}, pulse_curr:{pulse_current}"
root = tk.Tk()
name = dialog.asksaveasfilename(title='Save')
if name:  # if a name was entered, don't save otherwise
    if name[-4:] != '.txt':  # add .txt if not already there
        name = f'{name}.txt'
    np.savetxt(name, data, header=header, newline='\r\n', delimiter='\t')  # save
    print(f'Data saved as {name}')
else:
    print('Data not saved')

root.destroy()
plt.show()


#  todo: add code to show how to loop through N measurements using trigger