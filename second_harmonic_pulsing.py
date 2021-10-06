import instruments

import numpy as np
import matplotlib.pyplot as plt
import time

import tkinter as tk
import tkinter.messagebox as mb
from tkinter import filedialog as dialog

voltage = 31
width = 1e-3

num_points = 5000
num_loops = 2
frequency = 357
tc = 0.1

pulse1_assignments = {"I+": "B", "I-": "F"}
pulse2_assignments = {"I+": "D", "I-": "H"}
# pulse1_assignments = {"I+": "C", "I-": "G"}
# pulse2_assignments = {"I+": "G", "I-": "C"}

# measure_assignments = {"V1+": "C", "V1-": "G", "V2+": "C", "V2-": "G"}
# measure_assignments = {"V1+": "A", "V1-": "E", "V2+": "C", "V2-": "G"}
# measure_assignments = {}
# measure_assignments = {"V1+": "B", "V1-": "D", "V2+": "C", "V2-": "G"}
measure_assignments = {"V1+": "C", "V1-": "E", "V2+": "D", "V2-": "H"}
# measure_assignments = {"I+": "C", "I-": "G", "V1+": "C", "V1-": "G", "V2+": "E", "V2-": "A"}

top_lockin = instruments.SR830_RS232()
bot_lockin = instruments.SR830_RS232()
source = instruments.K6221()
sb = instruments.SwitchBox()
pg = instruments.K2461()
# dmm = instruments.K2000()


sb.connect(15)
source.connect_RS232(16)
top_lockin.connect(6)
bot_lockin.connect(10)
pg.connect()
root = tk.Tk()
base_name = dialog.asksaveasfilename(title='Define base name for files')
root.withdraw()
if not base_name == '':

    for probe_current in [5]:  # [0.01, 0.05, 0.1, 0.5, 1, 2, 2.5, 3, 3.5, 4, 4.5, 5]:
        print('starting with probe current as ' + str(probe_current) + 'mA')

        sb.switch(measure_assignments)

        source.sine_wave(frequency, probe_current)
        source.set_phase_marker()
        source.wave_output_on()

        time.sleep(2)

        top_lockin.set_harmonic(1)
        top_lockin.set_time_constant(tc)
        # top_lockin.auto_phase()
        top_lockin.set_phase(-90)
        top_lockin.set_harmonic(2)
        top_lockin.auto_range()
        # top_lockin.set_sensitivity(5e-2)
        top_lockin.set_filter(12)

        bot_lockin.set_harmonic(1)
        bot_lockin.set_time_constant(tc)
        # bot_lockin.auto_phase()
        bot_lockin.set_phase(-90)
        bot_lockin.set_harmonic(2)
        bot_lockin.auto_range()
        # top_lockin.set_sensitivity(5e-4)
        bot_lockin.set_filter(12)

        t_pos = np.zeros(num_points * num_loops)

        rxx_pos_r = np.zeros(num_points * num_loops)
        rxx_pos_theta = np.zeros(num_points * num_loops)

        rxy_pos_r = np.zeros(num_points * num_loops)
        rxy_pos_theta = np.zeros(num_points * num_loops)

        t_neg = np.zeros(num_points * num_loops)

        rxx_neg_r = np.zeros(num_points * num_loops)
        rxx_neg_theta = np.zeros(num_points * num_loops)

        rxy_neg_r = np.zeros(num_points * num_loops)
        rxy_neg_theta = np.zeros(num_points * num_loops)

        fig = plt.figure()
        fig.canvas.set_window_title(f'Iprobe = {probe_current}')
        rxx_ax = plt.subplot(211)
        rxy_ax = plt.subplot(212)

        rxx_pos_line, = rxx_ax.plot(t_pos, rxx_pos_r, 'k.')
        rxx_neg_line, = rxx_ax.plot(t_neg, rxx_neg_r, 'r.')
        rxx_ax.set_ylabel('R_xx (Ohms)')
        rxx_ax.ticklabel_format(useOffset=False)

        rxy_pos_line, = rxy_ax.plot(t_pos, rxy_pos_r, 'k.')
        rxy_neg_line, = rxy_ax.plot(t_neg, rxy_neg_r, 'r.')
        rxy_ax.set_ylabel('R_xy (Ohms)')
        rxy_ax.set_xlabel('Time (s)')
        rxy_ax.ticklabel_format(useOffset=False)
        # plt.show(block=False)
        plt.pause(0.001)
        time.sleep(10)

        start_time = time.time()
        pg.prepare_pulsing_voltage(voltage, width)
        for j in range(0, num_loops):
            print(f'pos pulse {j + 1}')
            source.wave_output_off()
            sb.switch(pulse1_assignments)
            time.sleep(500e-3)
            pg.send_pulse()
            time.sleep(500e-3)
            sb.switch(measure_assignments)
            time.sleep(500e-3)
            source.wave_output_on()
            # time.sleep(500e-3)
            time.sleep(1)
            for i in range(0, num_points):
                t_pos[i + j * num_points] = time.time() - start_time
                rxx_pos_r[i + j * num_points] = top_lockin.get_radius()
                # rxx_pos_r[i + j*num_points] = dmm.measure_one()*k2000_scaling
                rxx_pos_theta[i + j * num_points] = top_lockin.get_angle()
                rxy_pos_r[i + j * num_points] = bot_lockin.get_radius()
                rxy_pos_theta[i + j * num_points] = bot_lockin.get_angle()

            rxx_pos_line.set_data(t_pos, rxx_pos_r / (probe_current * 1e-3))
            rxy_pos_line.set_data(t_pos, rxy_pos_r / (probe_current * 1e-3))
            rxx_ax.relim()
            rxx_ax.autoscale_view()
            rxy_ax.relim()
            rxy_ax.autoscale_view()
            plt.pause(0.1)

            print(f'neg pulse {j + 1}')
            source.wave_output_off()
            sb.switch(pulse2_assignments)
            time.sleep(500e-3)
            pg.send_pulse()
            time.sleep(500e-3)
            sb.switch(measure_assignments)
            time.sleep(500e-3)
            source.wave_output_on()
            # time.sleep(500e-3)
            time.sleep(1)
            for i in range(0, num_points):
                t_neg[i + j * num_points] = time.time() - start_time
                rxx_neg_r[i + j * num_points] = top_lockin.get_radius()
                rxx_neg_theta[i + j * num_points] = top_lockin.get_angle()
                rxy_neg_r[i + j * num_points] = bot_lockin.get_radius()
                rxy_neg_theta[i + j * num_points] = bot_lockin.get_angle()

            rxx_neg_line.set_data(t_neg, rxx_neg_r / (probe_current * 1e-3))
            rxy_neg_line.set_data(t_neg, rxy_neg_r / (probe_current * 1e-3))
            rxx_ax.relim()
            rxx_ax.autoscale_view()
            rxy_ax.relim()
            rxy_ax.autoscale_view()
            plt.pause(0.1)



        data = np.column_stack(
            (t_pos, rxx_pos_r, rxx_pos_theta, rxy_pos_r, rxy_pos_theta, t_neg, rxx_neg_r, rxx_neg_theta,
             rxy_neg_r, rxy_neg_theta))
        name = base_name.replace('.txt', '') + '-probe-' + str(probe_current) + 'mA' + '.txt'
        if name:  # if a name was entered, don't save otherwise
            np.savetxt(name, data, newline='\r\n', delimiter='\t')  # save
            print(f'Data saved as {name}')
        else:
            print('Data not saved')
        source.wave_output_off()
        sb.reset_all()


    source.close()

    plt.show()
