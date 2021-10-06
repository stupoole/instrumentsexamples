import time
import numpy as np
import Instruments
import matplotlib.pyplot as plt

from tkinter import filedialog as dialog

pulse1_assignments = {"I+": "B", "I-": "F", "V1+": "C", "V1-": "E", "V2+": "D", "V2-": "H"}
pulse2_assignments = {"I+": "D", "I-": "H", "V1+": "E", "V1-": "G", "V2+": "F", "V2-": "B"}
measure_assignments = {"I+": "A", "I-": "E", "V1+": "B", "V1-": "D", "V2+": "C", "V2-": "G"}  # here V1 is Vxx
pulse_voltage = 35
pulse_width = 1e-3
probe_current = 200e-6
n_points = 1000
n_loops = 2

sb = Instruments.SwitchBox()
dmm = Instruments.K2000()
pg = Instruments.K2461()
scope = Instruments.DS1104()
error_sound = Instruments.error_sound
alert_sound = Instruments.alert_sound

sb.connect()
dmm.connect()
pg.connect()
scope.connect()

scope.set_trig_chan(4)
scope.prepare_for_4channel_pulse()
dmm.prepare_measure_one()
t_pos = np.array([])
t_scope_pos = np.array([])
Rxy_pos = np.array([])
Rxx_pos = np.array([])
Rxy_scope_pos = np.array([])
Rxx_scope_pos = np.array([])
I_scope_pos = np.array([])
t_neg = np.array([])
t_scope_neg = np.array([])
Rxy_neg = np.array([])
Rxx_neg = np.array([])
Rxy_scope_neg = np.array([])
Rxx_scope_neg = np.array([])
I_scope_neg = np.array([])

myfig = plt.figure("all plots")
rxx_ax = plt.subplot(221)
rxx_ax.clear()
rxx_pos_line, = rxx_ax.plot(t_pos, Rxx_pos, 'k.')
rxx_neg_line, = rxx_ax.plot(t_neg, Rxx_neg, 'r.')
# rxx_ax.set_xlabel('Time (s)')
rxx_ax.set_ylabel('R_xx (Ohms)')
rxx_ax.ticklabel_format(useOffset=False)

rxy_ax = plt.subplot(222)
rxy_ax.clear()
rxy_pos_line, = rxy_ax.plot(t_pos, Rxy_pos, 'k.')
rxy_neg_line, = rxy_ax.plot(t_neg, Rxy_neg, 'r.')
rxy_ax.set_xlabel('Time (s)')
rxy_ax.set_ylabel('R_xy (Ohms)')
rxy_ax.ticklabel_format(useOffset=False)
plt.show(block=False)

scope_ax1 = plt.subplot(324)
scope_ax1.clear()
scope_pos_line1, = scope_ax1.plot(t_scope_pos, I_scope_pos, 'k.')
scope_neg_line1, = scope_ax1.plot(t_scope_neg, I_scope_neg, 'r.')
# scope_ax1.set_xlabel('Time (s)')
scope_ax1.set_ylabel('50ohm Signal (V)')
scope_ax1.ticklabel_format(useOffset=False)

scope_ax2 = plt.subplot(325)
scope_ax2.clear()
scope_pos_line2, = scope_ax2.plot(t_scope_pos, Rxx_scope_pos, 'k.')
scope_neg_line2, = scope_ax2.plot(t_scope_neg, Rxx_scope_neg, 'r.')
# scope_ax2.set_xlabel('Time (s)')
scope_ax2.set_ylabel('Rxx Signal (V)')
scope_ax2.ticklabel_format(useOffset=False)
plt.show(block=False)

scope_ax3 = plt.subplot(326)
scope_ax3.clear()
scope_pos_line3, = scope_ax3.plot(t_scope_pos, Rxy_scope_pos, 'k.')
scope_neg_line3, = scope_ax3.plot(t_scope_neg, Rxy_scope_neg, 'r.')
scope_ax3.set_xlabel('Time (s)')
scope_ax3.set_ylabel('Rxy Signal (V)')
scope_ax3.ticklabel_format(useOffset=False)
plt.show(block=False)

mng = plt.get_current_fig_manager()
mng.frame.Maximize(True)
plt.pause(0.001)

start_time = time.time()
for loop_count in range(n_loops):
    print('Loop count:', loop_count + 1, 'Pulse: 1')
    sb.switch(pulse1_assignments)
    scope.single_trig()
    pg.prepare_pulsing_voltage(pulse_voltage, pulse_width)
    pg.set_ext_trig()
    time.sleep(200e-3)
    pulse_t = time.time()
    pg.send_pulse()
    time.sleep(200e-3)
    sb.switch(measure_assignments)
    pg.enable_4_wire_probe(probe_current)
    time.sleep(500e-3)
    t = np.zeros(n_points)
    vxx = np.zeros(n_points)
    vxy = np.zeros(n_points)
    curr = np.zeros(n_points)
    for meas_count in range(n_points):
        t[meas_count] = time.time()
        pg.trigger_fetch()
        dmm.trigger()
        vxx[meas_count], curr[meas_count] = pg.fetch_one()
        vxy[meas_count] = dmm.fetch_one()
    pg.disable_probe_current()
    t_pos = np.append(t_pos, t - start_time)
    Rxx_pos = np.append(Rxx_pos, vxx / curr)
    Rxy_pos = np.append(Rxy_pos, vxy / curr)
    scope_data = scope.get_data(30001, 60000, 1)
    I_scope_pos = np.append(I_scope_pos, scope_data)
    scope_data = scope.get_data(30001, 60000, 2)
    Rxx_scope_pos = np.append(Rxx_scope_pos, scope_data)
    scope_data = scope.get_data(30001, 60000, 3)
    Rxy_scope_pos = np.append(Rxy_scope_pos, scope_data)
    time_step = float(scope.get_time_inc())
    scope_time = np.array(range(0, len(scope_data))) * time_step + pulse_t - start_time
    t_scope_pos = np.append(t_scope_pos, scope_time)

    rxx_pos_line.set_data(t_pos, Rxx_pos)
    rxy_pos_line.set_data(t_pos, Rxy_pos)
    scope_pos_line1.set_data(t_scope_pos, I_scope_pos)
    scope_pos_line2.set_data(t_scope_pos, Rxx_scope_pos)
    scope_pos_line3.set_data(t_scope_pos, Rxy_scope_pos)
    rxx_ax.relim()
    rxx_ax.autoscale_view()
    rxy_ax.relim()
    rxy_ax.autoscale_view()
    scope_ax1.relim()
    scope_ax1.autoscale_view()
    scope_ax2.relim()
    scope_ax2.autoscale_view()
    scope_ax3.relim()
    scope_ax3.autoscale_view()

    myfig.canvas.draw()
    plt.pause(0.01)

    print('Loop count:', loop_count + 1, 'Pulse: 2')
    sb.switch(pulse2_assignments)
    scope.single_trig()
    pg.prepare_pulsing_voltage(pulse_voltage, pulse_width)
    pg.set_ext_trig()
    time.sleep(200e-3)
    pulse_t = time.time()
    pg.send_pulse()
    time.sleep(200e-3)
    sb.switch(measure_assignments)
    pg.enable_4_wire_probe(probe_current)
    time.sleep(500e-3)
    t = np.zeros(n_points)
    vxx = np.zeros(n_points)
    vxy = np.zeros(n_points)
    curr = np.zeros(n_points)
    for meas_count in range(n_points):
        t[meas_count] = time.time()
        pg.trigger_fetch()
        dmm.trigger()
        vxx[meas_count], curr[meas_count] = pg.fetch_one()
        vxy[meas_count] = dmm.fetch_one()
    pg.disable_probe_current()
    t_neg = np.append(t_neg, t - start_time)
    Rxx_neg = np.append(Rxx_neg, vxx / curr)
    Rxy_neg = np.append(Rxy_neg, vxy / curr)
    scope_data = scope.get_data(30001, 60000, 1)
    I_scope_neg = np.append(I_scope_neg, scope_data)
    scope_data = scope.get_data(30001, 60000, 2)
    Rxx_scope_neg = np.append(Rxx_scope_neg, scope_data)
    scope_data = scope.get_data(30001, 60000, 3)
    Rxy_scope_neg = np.append(Rxy_scope_neg, scope_data)
    time_step = float(scope.get_time_inc())
    scope_time = np.array(range(0, len(scope_data))) * time_step + pulse_t - start_time
    t_scope_neg = np.append(t_scope_neg, scope_time)

    rxx_neg_line.set_data(t_neg, Rxx_neg)
    rxy_neg_line.set_data(t_neg, Rxy_neg)
    scope_neg_line1.set_data(t_scope_neg, I_scope_neg)
    scope_neg_line2.set_data(t_scope_neg, Rxx_scope_neg)
    scope_neg_line3.set_data(t_scope_neg, Rxy_scope_neg)
    rxx_ax.relim()
    rxx_ax.autoscale_view()
    rxy_ax.relim()
    rxy_ax.autoscale_view()
    scope_ax1.relim()
    scope_ax1.autoscale_view()
    scope_ax2.relim()
    scope_ax2.autoscale_view()
    scope_ax3.relim()
    scope_ax3.autoscale_view()

    myfig.canvas.draw()
    plt.pause(0.01)

sb.reset_all()
alert_sound()
data = np.column_stack(
    (t_pos,
     Rxx_pos,
     Rxy_pos,
     t_neg,
     Rxx_neg,
     Rxy_neg,
     t_scope_pos,
     I_scope_pos,
     Rxx_scope_pos,
     Rxy_scope_pos,
     t_scope_neg,
     I_scope_neg,
     Rxx_scope_neg,
     Rxy_scope_neg,
     ))
name = dialog.asksaveasfilename(title='Save')
if name:  # if a name was entered, don't save otherwise
    if name[-4:] != '.txt':  # add .txt if not already there
        name = f'{name}.txt'
    np.savetxt(name, data, newline='\r\n', delimiter='\t')  # save
    print(f'Data saved as {name}')
else:
    print('Data not saved')

plt.show()