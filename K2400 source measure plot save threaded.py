import instruments
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import threading
import queue
import time
import numpy as np
from tkinter import filedialog as dialog

matplotlib.use('Qt5Agg')


class Plotter:
    """

    """

    def __init__(self, port, meas_curr, max_time):
        self.max_time = max_time
        self.source_meter = instruments.K2400()
        self.source_meter.connect(port)
        self.current = meas_curr
        self.plot_queue = queue.Queue()
        self._is_running = True
        threading.Thread(target=self.get_data, daemon=True).start()
        self.do_plotting()

    def get_data(self):
        self.source_meter.prepare_measure_one(self.current)
        self.source_meter.use_rear_io(False)
        self.source_meter.enable_output_current()
        while self._is_running:
            t, v, c = self.source_meter.read_one()
            self.plot_queue.put((t, v, c))
            time.sleep(0.25)

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

                indices = [ind for ind, val in enumerate(times) if val > times[-1] - self.max_time]
                plot_times = [times[i] - times[0] for i in indices]
                plot_resistances = [resistances[i] for i in indices]

                resistance_line.set_xdata(plot_times)
                resistance_line.set_ydata(plot_resistances)
                ax.relim()
                ax.autoscale_view()

                figure.canvas.draw()
                figure.canvas.flush_events()
        header = "Time (s), Voltage (V), Current (A), Resistance (Ohms)"
        data = np.column_stack((np.array(times), np.array(voltages), np.array(currents), np.array(resistances)))
        instruments.filehandler.save(data, header)

    def stop_button_callback(self, event):
        self._is_running = False
        self.source_meter.disable_output_current()
        self.source_meter.close()


if __name__ == '__main__':
    current = 0.1e-3
    plotter = Plotter(6, current, 30000)
