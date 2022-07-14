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

        print(f'Switching to {settings["assignment"]}')
        self.sb.switch(settings["assignment"])
        time.sleep(1)
        print('Arming pulse')
        self.source.arm_pulse_sweep()
        time.sleep(2)
        print('Starting measurement')

        while self._is_running:
            probe_time = time.time()
            self.source.trigger()
            time.sleep(0.5)
            data = self.source.get_trace()
            voltage_data = data[0::2]
            time_data = data[1::2] + probe_time
            self.plot_queue.put((time_data, voltage_data, self.currents))

    def do_plotting(self):
        times = []
        currents = []
        voltages = []
        resistances = []
        figure = plt.figure(1)
        figure.canvas.set_window_title('Resistance Plots')
        ax = figure.add_subplot(111)
        plt.xlabel('Time(s)')
        plt.ylabel('Resistance (Ohms)')
        resistance_line, = ax.plot(times, resistances, 'r-')
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
                times.append(t)
                currents.append(c)
                voltages.append(v)
                resistances.append(v / c)

                indices = [ind for ind, val in enumerate(times) if val > times[-1] - self.settings["max_time"]]
                plot_times = [times[i] - times[0] for i in indices]
                plot_resistances = [resistances[i] for i in indices]

                resistance_line.set_xdata(plot_times)
                resistance_line.set_ydata(plot_resistances)
                ax.relim()
                ax.autoscale_view()

                figure.canvas.draw()
                figure.canvas.flush_events()
        meta_df = pd.DataFrame(settings.update({"absolute_reference_time": self.absolute_reference_time}))
        data_df = pd.DataFrame({'I': currents, 'V': voltages, 't': times, 'probe': ass_to_str(settings["assignment"]),
                                'type': 'contiuous'})
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
        "delay": 1,
        "repeats": 1,
        "channel": 1,
        "volt_range": 100e-3,  # 10 for Rxx # 100e-3 for Rxy sweep 1
        "width": 500e-6,
        "compliance": 40,
        "bias": 0.0,
        "assignment": {"I+": "A", "I-": "E", "V2+": "C", "V2-": "G"},
        "sb_port": 11,
        "max_time": 3600
    }

    plotter = DeltaPlotter(settings)
