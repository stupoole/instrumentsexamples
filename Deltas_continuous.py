import instruments
import pandas as pd
import threading
import queue
import numpy as np
import matplotlib.pyplot as plt
import time
from matplotlib.widgets import Button
import tkinter as tk
import tkinter.messagebox as mb
from tkinter import filedialog as dialog
import matplotlib

matplotlib.use('Qt5Agg')


def ass_to_str(assignment):
    ass_string = str(assignment.values()).strip()
    string = ",".join(x for x in ass_string if x.isalpha()).replace('d,i,c,t,v,a,l,u,e,s,', '').upper()
    if string.strip() == "":
        string = ",".join(x for x in ass_string if x.isnumeric())
    return string


class DeltaPlotter:
    """

    """

    def __init__(self, settings):
        self.settings = settings
        self.currents = [settings["pulse_current"], -settings["pulse_current"]]
        self.sb = instruments.SwitchBox()
        self.final_dataframe = pd.DataFrame()
        self.source = instruments.K6221()
        self.source.connect_ethernet()
        self.plot_queue = queue.Queue()
        self.absolute_reference_time = time.time()
        self._is_running = True
        threading.Thread(target=self.get_data, daemon=True).start()
        self.do_plotting()

    def get_data(self):
        self.sb.connect(settings["sb_port"])
        self.source.set_compliance(settings["compliance"])
        self.source.set_sense_chan_and_range(settings["channel"], settings["volt_range"])
        self.source.configure_custom_sweep(self.currents, settings["delay"], settings["compliance"],
                                           settings["repeats"], settings["bias"], 'best')
        self.source.configure_pulse(settings["width"], 1, 1)

        print(f'Switching to {settings["assignment"][0]}')
        self.sb.switch(settings["assignment"][0])
        time.sleep(1)
        print('Arming pulse')
        self.source.arm_pulse_sweep()

        time.sleep(2)
        print('Starting measurement')

        while self._is_running:
            probe_time = time.time() - self.absolute_reference_time
            self.source.trigger()
            time.sleep(1)
            data = self.source.get_trace_fast()
            voltage_data = data[0::2]
            time_data = data[1::2] + probe_time
            self.plot_queue.put((time_data, voltage_data, self.currents))

    def do_plotting(self):
        times_pos = []
        times_neg = []
        currents_pos = []
        currents_neg = []
        voltages_pos = []
        resistances_pos = []
        voltages_neg = []
        resistances_neg = []
        figure = plt.figure(1)
        figure.canvas.set_window_title('Resistance Plots')
        ax = figure.add_subplot(111)
        plt.xlabel('Time(s)')
        plt.ylabel('Resistance (Ohms)')
        resistance_pos_line, = ax.plot(times_pos, resistances_pos, 'b+--')
        resistance_neg_line, = ax.plot(times_neg, resistances_neg, 'r+--')
        stop_button_axes = plt.axes([0.81, 0.025, 0.1, 0.055])
        stop_button = Button(stop_button_axes, 'Stop')
        stop_button.on_clicked(self.stop_button_callback)
        ax.grid()
        ax.ticklabel_format(useOffset=False)
        plt.draw()
        plt.show(block=False)
        while self._is_running:
            while not self.plot_queue.empty():
                t, v, c = self.plot_queue.get()

                times_pos.append(t[0])
                currents_pos.append(c[0])
                voltages_pos.append(v[0])
                resistances_pos.append(v[0] / c[0])

                times_neg.append(t[1])
                currents_neg.append(c[1])
                voltages_neg.append(v[1])
                resistances_neg.append(v[1] / c[1])

                indices = [ind for ind, val in enumerate(times_pos) if val > times_pos[-1] - self.settings["max_time"]]
                plot_pos_times = [times_pos[i] - times_pos[0] for i in indices]
                plot_pos_resistances = [resistances_pos[i] for i in indices]
                resistance_pos_line.set_xdata(plot_pos_times)
                resistance_pos_line.set_ydata(plot_pos_resistances)
                plot_neg_times = [times_neg[i] - times_pos[0] for i in indices]
                plot_neg_resistances = [resistances_neg[i] for i in indices]
                resistance_neg_line.set_xdata(plot_neg_times)
                resistance_neg_line.set_ydata(plot_neg_resistances)

                ax.relim()
                ax.autoscale_view()

                figure.canvas.draw()
                figure.canvas.flush_events()

        settings.update({"absolute_reference_time": self.absolute_reference_time})
        meta_df = pd.DataFrame(settings)
        data_df = pd.DataFrame(
            {'I+': currents_pos, 'V+': voltages_pos, 't+': times_pos, 'I-': currents_neg, 'V-': voltages_neg,
             't-': times_neg, 'probe': ass_to_str(settings["assignment"][0]), 'type': 'contiuous'})
        name = dialog.asksaveasfilename(title='Save')
        name = name.replace('.txt', '')
        name = name.replace('.hdf', '')
        name = name.replace('.h5', '')
        name = name.replace('.hd5', '')
        name += '.h5'
        if name:  # if a name was entered, don't save otherwise
            store = pd.HDFStore(name)
            store['meta_data'] = meta_df
            store['data'] = data_df
            print(f'Data saved as {name}')
            store.close()
        else:
            print('Data not saved')

    def stop_button_callback(self, event):
        self._is_running = False
        self.source.wave_output_off()
        self.source.close()
        self.sb.close()


if __name__ == '__main__':
    settings = {
        "pulse_current": 15e-3,  # Used 15mA to RC124 10um, 10mA for RC123 10um UJ, 5mA for RC123 5um UJ
        "delay": 0.25,
        "repeats": 1,
        "channel": 1,
        "volt_range": 1000e-3,  # 10 for Rxx # 100e-3 for Rxy sweep 1
        "width": 500e-6,
        "compliance": 40,
        "bias": 0.0,
        "assignment": [{"I+": "A", "I-": "E", "V2+": "C", "V2-": "G"}],
        "sb_port": 5,
        "max_time": 3600
    }

    plotter = DeltaPlotter(settings)
