import instruments
import matplotlib.pyplot as plt
import numpy as np
import time
from tkinter import filedialog as dialog

measure_assignments = {"I+": "A", "I-": "C", "V1+": "G", "V1-": "E"}
probe_current = 200e-6
start_t = 30
end_t = 21
end_wait_time = 600
time_values = np.array([])
Rxx = np.array([])
Rxy = np.array([])
temp = np.array([])

error_sound = instruments.error_sound
alert_sound = instruments.alert_sound

# sb = instruments.SwitchBox()
dmm = instruments.K2000()
pg = instruments.K2461()

tec = instruments.TEC1089SV()
# sb.connect(15)
dmm.connect(10)
pg.connect()
tec.connect(14)


tec.disable_control()
tec.set_ramp_rate(0.02)
# tec.set_target_temperature(start_t)
# tec.enable_control()
# while tec.get_temp_stability_state() is not "stable":
#     time.sleep(0.5)
# print('Temp stable')
# sb.switch(measure_assignments)
time.sleep(0.5)
dmm.prepare_measure_one()
pg.enable_4_wire_probe(probe_current)
time.sleep(0.5)

fig = plt.figure()
plt.ion()
rxx_ax = plt.subplot(311)
rxx_ax.clear()
rxx_line, = rxx_ax.plot(time_values, Rxx, 'k')
# rxx_ax.set_xlabel('Time (s)')
rxx_ax.set_ylabel('R_xx (Ohms)')
rxx_ax.ticklabel_format(useOffset=False)

rxy_ax = plt.subplot(312)
rxy_ax.clear()
rxy_line, = rxy_ax.plot(time_values, Rxy, 'k')
# rxy_ax.set_xlabel('Time (s)')
rxy_ax.set_ylabel('R_xy (Ohms)')
rxy_ax.ticklabel_format(useOffset=False)
plt.show(block=False)

temp_ax = plt.subplot(313)
temp_ax.clear()
temp_line, = temp_ax.plot(time_values, temp, 'k')
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
    t = time.time() - start_time
    pg.trigger_before_fetch()
    dmm.trigger()
    temp = np.append(temp, tec.get_object_temperature())
    vxx, curr = pg.fetch_one()
    vxy = dmm.fetch_one()

    Rxx = np.append(Rxx, vxx / curr)
    Rxy = np.append(Rxy, vxy / curr)
    time_values = np.append(time_values, t)

    rxx_line.set_data(time_values, Rxx)
    rxy_line.set_data(time_values, Rxy)
    temp_line.set_data(time_values, temp)
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
    t = time.time() - start_time
    pg.trigger_before_fetch()
    dmm.trigger()
    temp = np.append(temp, tec.get_object_temperature())
    vxx, curr = pg.fetch_one()
    vxy = dmm.fetch_one()

    Rxx = np.append(Rxx, vxx / curr)
    Rxy = np.append(Rxy, vxy / curr)
    time_values = np.append(time_values, t)

    rxx_line.set_data(time_values, Rxx)
    rxy_line.set_data(time_values, Rxy)
    temp_line.set_data(time_values, temp)
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
    (time_values,
     Rxx,
     Rxy,
     temp,
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
