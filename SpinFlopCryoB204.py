import instruments
import matplotlib
import matplotlib.ticker as ticker
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import threading
import queue
import time
import numpy as np
from tkinter import filedialog as dialog

matplotlib.use('Qt5Agg')


def save(data, header):
    name = dialog.asksaveasfilename(title='Save data')
    if name:  # if a name was entered, don't save otherwise
        if name[-4:] != '.txt':  # add .txt if not already there
            name = f'{name}.txt'
        np.savetxt(name, data, header=header, newline='\r\n', delimiter='\t')  # save
        print(f'Data saved as {name}')
    else:
        print('Data not saved')


class Plotter:
    """

    """

    def __init__(self, ports, ranges, meas_curr):
        """
        Plots in a loop. Shows all data. For measuring 2 Rxy values and Rxx and Field (in volts) simultaneously. Calibration still to be done.
        @param list-like ports: list of ports used in the following order: K2400, K2000 for first arm Rxy, K2000 for second arm Rxy, K2000 for field output.
        @param list-like ranges: list of measurement ranges used in the same order as for ports. In Volts.
        @param float meas_curr: probe current in Amps provided by K2400
        """
        self._field_calibration = 15e-3  # V/T
        self.source_meter = instruments.K2400()
        self.sense_meter = instruments.K2400()
        self.rxy_1_meter = instruments.K2000()
        self.rxy_2_meter = instruments.K2000()
        self.field_meter = instruments.K2000()

        self.source_meter.connect(ports[0])
        self.sense_meter.connect(ports[1])
        self.rxy_1_meter.connect(ports[2])
        self.rxy_2_meter.connect(ports[3])
        self.field_meter.connect(ports[4])

        self.source_meter.prepare_measure_one(meas_curr, ranges[0])
        self.sense_meter.prepare_measure_only(ranges[1])
        self.rxy_1_meter.prepare_measure_one(ranges[2])
        self.rxy_2_meter.prepare_measure_one(ranges[3])
        self.field_meter.prepare_measure_one(ranges[4])

        self.source_meter.use_rear_io(False)

        self.source_meter.enable_output_current()
        self.sense_meter.enable_output_current()

        self.plot_queue = queue.Queue()
        self._is_running = True
        threading.Thread(target=self._get_data, daemon=True).start()
        self._do_plotting()

    def _get_data(self):
        while self._is_running:
            self.source_meter.trigger()
            self.sense_meter.trigger()
            self.rxy_1_meter.trigger()
            self.rxy_2_meter.trigger()
            self.field_meter.trigger()

            t, v_xx1, c = self.source_meter.fetch_one()
            t2, v_xx2, c2 = self.sense_meter.fetch_one()
            v_xy1 = self.rxy_1_meter.fetch_one()
            v_xy2 = self.rxy_2_meter.fetch_one()
            field_voltage = self.field_meter.fetch_one()
            self.plot_queue.put((t, c, v_xx1, v_xx2, v_xy1, v_xy2, field_voltage))
            time.sleep(0.25)

    def _do_plotting(self):
        times = []
        currents = []
        v_xx1_values = []
        v_xx2_values = []
        v_xy1_values = []
        v_xy2_values = []
        r_xx1_values = []
        r_xx2_values = []
        r_xy1_values = []
        r_xy2_values = []
        field_voltages = []
        field_values = []
        fig = plt.figure()
        fig.canvas.set_window_title('Resistance Plots')
        ax_xx = fig.add_subplot(311)
        ax_xx.grid()
        ax_xx.ticklabel_format(useOffset=False)
        # plt.xlabel('Time(s)')
        plt.ylabel('R_xx (Ohms)')
        ax_xy = fig.add_subplot(312)
        ax_xy.grid()
        # ax_xx.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.1f}'))
        ax_xy.ticklabel_format(useOffset=False)
        # ax_xy.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.4f}'))
        plt.xlabel('Field (T)')
        plt.ylabel('R_xy (Ohms)')

        ax_field = fig.add_subplot(313)
        ax_field.grid()
        # ax_field.yaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.1f}'))
        ax_field.ticklabel_format(useOffset=False)
        plt.xlabel('Time (s)')
        plt.ylabel('Field (T)')

        r_xx1_line, = ax_xx.plot(field_voltages, r_xx1_values, 'r-')
        r_xx2_line, = ax_xx.plot(field_voltages, r_xx2_values, 'b-')
        r_xy1_line, = ax_xy.plot(field_voltages, r_xy1_values, 'r-')
        r_xy2_line, = ax_xy.plot(field_voltages, r_xy2_values, 'b-')
        field_line, = ax_field.plot(times, field_voltages, 'k-')
        stop_button_axes = plt.axes([0.81, 0.025, 0.1, 0.055])
        stop_button = Button(stop_button_axes, 'Stop')
        stop_button.on_clicked(self._stop_button_callback)

        plt.show(block=False)
        while self._is_running:
            while not self.plot_queue.empty():
                t, c, v_xx1, v_xx2, v_xy1, v_xy2, field_voltage = self.plot_queue.get()
                times.append(t)
                currents.append(c)
                v_xx1_values.append(v_xx1)
                r_xx1_values.append(v_xx1 / c)
                v_xx2_values.append(v_xx2)
                r_xx2_values.append(v_xx2 / c)
                v_xy1_values.append(v_xy1)
                r_xy1_values.append(v_xy1 / c)
                v_xy2_values.append(v_xy2)
                r_xy2_values.append(v_xy2 / c)
                field_voltages.append(field_voltage)
                field_values.append(field_voltage/self._field_calibration)


                r_xx1_line.set_xdata(field_values)
                r_xx1_line.set_ydata(r_xx1_values)
                r_xx2_line.set_xdata(field_values)
                r_xx2_line.set_ydata(r_xx2_values)
                r_xy1_line.set_xdata(field_values)
                r_xy1_line.set_ydata(r_xy1_values)
                r_xy2_line.set_xdata(field_values)
                r_xy2_line.set_ydata(r_xy2_values)
                field_line.set_xdata([t - times[0] for t in times])
                field_line.set_ydata(field_values)

                ax_xx.relim()
                ax_xx.autoscale_view()
                ax_xy.relim()
                ax_xy.autoscale_view()
                ax_field.relim()
                ax_field.autoscale_view()

            fig.canvas.draw()
            fig.canvas.flush_events()
        header = "Time (s), Current (A), V_xx1 (V), V_xx2 (V), V_xy1 (V), V_xy2 (V), Field Voltages (V)"
        data = np.column_stack((np.array(times),
                                np.array(currents),
                                np.array(v_xx1_values),
                                np.array(v_xx2_values),
                                np.array(v_xy1_values),
                                np.array(v_xy2_values),
                                np.array(field_voltages)))
        save(data, header)

    def _stop_button_callback(self, event):
        self._is_running = False
        self.source_meter.disable_output_current()
        self.sense_meter.disable_output_current()
        self.sense_meter.close()
        self.source_meter.close()


if __name__ == '__main__':
    source_port = 6
    sense_port = 11
    r_xy1_port = 8
    r_xy2_port = 9
    field_port = 10

    source_volt_range = 0
    dmm_volt_range = 0
    field_volt_range = 0

    probe_current = 0.2e-3

    ports_tuple = (source_port, sense_port, r_xy1_port, r_xy2_port, field_port)

    ranges_tuple = (source_volt_range, source_volt_range, dmm_volt_range, dmm_volt_range, field_volt_range)

    plotter = Plotter(ports_tuple, ranges_tuple, probe_current)
