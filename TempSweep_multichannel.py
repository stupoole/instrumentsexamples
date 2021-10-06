import instruments
import matplotlib.pyplot as plt
import numpy as np
import time
from tkinter import filedialog as dialog

probe_current = 100e-6
start_t = -15
end_t = 21
end_wait_time = 3000
time_xx = np.array([])
time_xy = np.array([])
Rxx1 = np.array([])
Rxx2 = np.array([])
Rxy1 = np.array([])
Rxy2 = np.array([])
temp_xx = np.array([])
temp_xy = np.array([])

meas_ass1 = {"I+": "A", "I-": "F", "V1+": "B", "V1-": "C", "V2+": "D", "V2-": "E"}
meas_ass2 = {"I+": "A", "I-": "F", "V1+": "C", "V1-": "H", "V2+": "D", "V2-": "G"}

error_sound = instruments.error_sound
alert_sound = instruments.alert_sound

sb = instruments.SwitchBox()
dmm = instruments.K2000()
pg = instruments.K2461()

tec = instruments.TEC1089SV()
sb.connect(18)
dmm.connect(10)
pg.connect()
tec.connect(14)

tec.disable_control()
tec.set_ramp_rate(0.005)
tec.set_target_temperature(start_t)
tec.enable_control()
while tec.get_temp_stability_state() is not "stable":
    time.sleep(0.5)
print('Temp stable')

# sb.switch(meas_ass1)
# time.sleep(0.5)
# pg.enable_4_wire_probe(probe_current)
# dmm.prepare_measure_one()
# time.sleep(0.5)

fig = plt.figure()
plt.ion()
rxx_ax = plt.subplot(311)
rxx_ax.clear()
rxx_line, = rxx_ax.plot(time_xx, Rxx1, 'k')
# rxx_ax.set_xlabel('Time (s)')
rxx_ax.set_ylabel('R_xx (Ohms)')
rxx_ax.ticklabel_format(useOffset=False)

rxy_ax = plt.subplot(312)
rxy_ax.clear()
rxy_line, = rxy_ax.plot(time_xy, Rxy1, 'k')
# rxy_ax.set_xlabel('Time (s)')
rxy_ax.set_ylabel('R_xy (Ohms)')
rxy_ax.ticklabel_format(useOffset=False)
plt.show(block=False)

temp_ax = plt.subplot(313)
temp_ax.clear()
temp_line, = temp_ax.plot(time_xy, temp_xy, 'k')
temp_ax.set_xlabel('Time (s)')
temp_ax.set_ylabel('Temperature (C)')
temp_ax.ticklabel_format(useOffset=False)
plt.show(block=False)

tec.disable_control()
print('sleeping')
plt.pause(10)
print('woke')
tec.set_target_temperature(end_t)
tec.enable_control()

plt.pause(1)

start_time = time.time()
while tec.get_temp_stability_state() is not "stable":
    sb.switch(meas_ass1)
    time.sleep(0.5)
    pg.enable_4_wire_probe(probe_current)
    dmm.prepare_measure_one()
    time.sleep(0.5)
    t = time.time() - start_time
    pg.trigger_before_fetch()
    dmm.trigger()
    temp_xx = np.append(temp_xx, tec.get_object_temperature())
    vxx1, curr = pg.fetch_one()
    vxx2 = dmm.fetch_one()
    pg.disable_probe_current()
    Rxx1 = np.append(Rxx1, np.array([vxx1 / curr]))
    Rxx2 = np.append(Rxx2, np.array([vxx2 / curr]))
    time_xx = np.append(time_xx, t)

    sb.switch(meas_ass2)
    time.sleep(0.5)
    pg.enable_4_wire_probe(probe_current)
    dmm.prepare_measure_one()
    time.sleep(0.5)
    t = time.time() - start_time
    pg.trigger_before_fetch()
    dmm.trigger()
    temp_xy = np.append(temp_xy, tec.get_object_temperature())
    vxy1, curr = pg.fetch_one()
    vxy2 = dmm.fetch_one()
    pg.disable_probe_current()
    Rxy1 = np.append(Rxy1, np.array([vxy1 / curr]))
    Rxy2 = np.append(Rxy2, np.array([vxy2 / curr]))
    time_xy = np.append(time_xy, t)

    rxx_line.set_data(time_xx, Rxx1)
    rxy_line.set_data(time_xy, Rxy2)
    temp_line.set_data(time_xy, temp_xy)
    rxx_ax.relim()
    rxx_ax.autoscale_view()
    rxy_ax.relim()
    rxy_ax.autoscale_view()
    temp_ax.relim()
    temp_ax.autoscale_view()
    fig.canvas.draw()
    plt.draw()
    plt.pause(5)

toc = time.time()
tic = 0

print(f"Target reached. Measuring for {end_wait_time} seconds")
while tic < end_wait_time:
    sb.switch(meas_ass1)
    time.sleep(0.5)
    pg.enable_4_wire_probe(probe_current)
    dmm.prepare_measure_one()
    time.sleep(0.5)
    t = time.time() - start_time
    pg.trigger_before_fetch()
    dmm.trigger()
    temp_xx = np.append(temp_xx, tec.get_object_temperature())
    vxx1, curr = pg.fetch_one()
    vxx2 = dmm.fetch_one()
    pg.disable_probe_current()
    Rxx1 = np.append(Rxx1, np.array([vxx1 / curr]))
    Rxx2 = np.append(Rxx2, np.array([vxx2 / curr]))
    time_xx = np.append(time_xx, t)

    sb.switch(meas_ass2)
    time.sleep(0.5)
    pg.enable_4_wire_probe(probe_current)
    dmm.prepare_measure_one()
    time.sleep(0.5)
    t = time.time() - start_time
    pg.trigger_before_fetch()
    dmm.trigger()
    temp_xy = np.append(temp_xy, tec.get_object_temperature())
    vxy1, curr = pg.fetch_one()
    vxy2 = dmm.fetch_one()
    pg.disable_probe_current()
    Rxy1 = np.append(Rxy1, np.array([vxy1 / curr]))
    Rxy2 = np.append(Rxy2, np.array([vxy2 / curr]))
    time_xy = np.append(time_xy, t)

    rxx_line.set_data(time_xx, Rxx1)
    rxy_line.set_data(time_xy, Rxy1)
    temp_line.set_data(time_xy, temp_xy)
    rxx_ax.relim()
    rxx_ax.autoscale_view()
    rxy_ax.relim()
    rxy_ax.autoscale_view()
    temp_ax.relim()
    temp_ax.autoscale_view()
    fig.canvas.draw()
    plt.draw()
    plt.pause(5)

    tic = time.time()-toc

data = np.column_stack(
    (time_xx,
     temp_xx,
     Rxx1,
     Rxx2,
     time_xy,
     temp_xy,
     Rxy1,
     Rxy2
     ))

name = dialog.asksaveasfilename(title='Save')
if name:  # if a name was entered, don't save otherwise
    if name[-4:] != '.txt':  # add .txt if not already there
        name = f'{name}.txt'
    np.savetxt(name, data, newline='\r\n', delimiter='\t')  # save
    print(f'Data saved as {name}')
else:
    print('Data not saved')

pg.disable_probe_current()
pg.close()
dmm.close()
# sb.close()
tec.close()

plt.show()
