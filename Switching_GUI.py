import sys
import time
from tqdm import tqdm
import instruments
import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pyvisa
import serial
from PyQt5 import QtCore, QtWidgets, uic
import pandas as pd

# Todo: replace tkinter boxes with qt

matplotlib.use('Qt5Agg')

error_sound = instruments.error_sound
alert_sound = instruments.alert_sound


def assignment_to_str(assignment):
    return str(assignment).replace('\'', '')


class DataCollector(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    pos_data_ready = QtCore.pyqtSignal(np.ndarray, np.ndarray, np.ndarray)
    pos_scope_data_ready = QtCore.pyqtSignal(np.ndarray, np.ndarray)
    pos_tec_data_ready = QtCore.pyqtSignal(np.ndarray, np.ndarray)
    neg_data_ready = QtCore.pyqtSignal(np.ndarray, np.ndarray, np.ndarray)
    neg_scope_data_ready = QtCore.pyqtSignal(np.ndarray, np.ndarray)
    neg_tec_data_ready = QtCore.pyqtSignal(np.ndarray, np.ndarray)
    finished_res_measurement = QtCore.pyqtSignal(np.ndarray, np.ndarray)
    stable = QtCore.pyqtSignal()

    mutex = QtCore.QMutex()
    mutex.lock()
    is_stopped = False
    mutex.unlock()

    sb = instruments.SwitchBox()
    bb = instruments.BalanceBox()
    dmm = instruments.K2000()
    pg = instruments.K2461()
    scope = instruments.DS1104()
    tec = instruments.TEC1089SV()

    scope_enabled = False
    tec_enabled = False

    # reference_resistance = 10.0154663186062
    reference_resistance = 50.036
    two_wire = 150

    @QtCore.pyqtSlot(dict)
    def start_measurement(self, settings):
        self.assignments = settings["assignments"]
        mode = settings["pulse_type"]
        sb_port = settings["sb_port"]
        bb_port = settings["bb_port"]
        dmm_port = settings["dmm_port"]
        pulse_mag = settings["pulse_mag"]
        pulse_width = settings["pulse_width"]
        meas_curr = settings["probe_current"]
        meas_n = settings["measurement_count"]
        loop_n = settings["loop_count"]
        bb_enabled = settings["bb_enabled"]
        scope_enabled = settings["scope_enabled"]

        self.mutex.lock()
        self.is_stopped = False
        self.mutex.unlock()

        error_flag, is_voltage_pulse, pulse_mag, pulse_width, meas_curr, meas_n, loop_n = self.handle_inputs(mode,
                                                                                                        sb_port,
                                                                                                        bb_port,
                                                                                                        dmm_port,
                                                                                                        pulse_mag,
                                                                                                        pulse_width,
                                                                                                        meas_curr,
                                                                                                        meas_n, loop_n,
                                                                                                        bb_enabled,
                                                                                                        scope_enabled)
        # If flag is true then something failed in parsing the inputs or connecting and the loop will not continue.
        if error_flag:
            return

        self.pulse_and_measure(is_voltage_pulse, pulse_mag, pulse_width, meas_curr,
                               meas_n, loop_n)

        self.sb.close()
        if bb_enabled:
            self.bb.close()
        if scope_enabled:
            self.scope.close()
        self.dmm.close()
        self.pg.close()
        # plt.pause()(1)
        self.finished.emit()


    @QtCore.pyqtSlot(str, str, str, str, str, str, str, str, str, bool)
    def resistance_measurement(self, mode, sb_port, bb_port, dmm_port, pulse_mag, pulse_width, meas_curr, meas_n,
                               loop_n, bb_enabled):
        self.mutex.lock()
        self.is_stopped = False
        self.mutex.unlock()

        # Converts the strings in the gui boxes into appropriate types and then connects and sets up instruments.
        error_flag, pulse_volts, pulse_mag, pulse_width, meas_curr, meas_n, loop_n = self.handle_inputs(mode,
                                                                                                        sb_port,
                                                                                                        bb_port,
                                                                                                        dmm_port,
                                                                                                        pulse_mag,
                                                                                                        pulse_width,
                                                                                                        meas_curr,
                                                                                                        meas_n, loop_n,
                                                                                                        bb_enabled,
                                                                                                        False)

        # If something fails to connect, the UI doesn't continue
        if error_flag:
            return

        # reset the resistances to measure two wires properly
        if bb_enabled:
            self.bb.reset_resistances()

        two_wires = np.zeros(len(self.assignments["two_wire_assignments"]))
        four_wires = np.zeros(len(self.assignments["four_wire_assignments"]))

        for i in range(len(self.assignments["two_wire_assignments"])):
            self.sb.switch(self.assignments["two_wire_assignments"][i])
            time.sleep(0.3)
            self.pg.enable_2_wire_probe(meas_curr)
            time.sleep(0.2)
            c, v = self.pg.read_one()
            two_wires[i] = v / c
            self.pg.disable_probe_current()
        print('Two Wires: ', two_wires)

        for i in range(len(self.assignments["four_wire_assignments"])):
            self.sb.switch(self.assignments["four_wire_assignments"][i])
            time.sleep(0.3)
            self.pg.enable_4_wire_probe(meas_curr)
            time.sleep(0.2)
            c, v = self.pg.read_one()
            four_wires[i] = v / c
            self.pg.disable_probe_current()
        print('Four Wires: ', four_wires)

        if bb_enabled:
            self.bb.close()
        self.dmm.close()
        self.pg.close()
        self.sb.close()
        self.finished_res_measurement.emit(two_wires, four_wires)


    @QtCore.pyqtSlot(int, str, str)
    def start_TEC_temperature_control(self, system, port, target):
        # System: 0 -> none, 1-> TEC 2-> anything else, for future (HTS?)
        self.tec_enabled = True
        if system == 0:
            return
        try:
            port = int(port)
            target = float(target)
        except ValueError:
            print('Failed to convert strings to numbers. Check port and target temp boxes')
            return
        if system == 1:
            try:
                self.tec.connect(port)
                self.tec.set_target_temperature(target)
                self.tec.enable_control()
            except pyvisa.pyvisaIOError:
                print(f'Could not connect to TEC on port {port} or could not set temperature to {target}')
                self.stable.emit()
                return

            a = self.tec.get_temp_stability_state()
            while a != "stable":
                time.sleep(1)
                a = self.tec.get_temp_stability_state()
            self.stable.emit()
        # if system == 2:
        #     try:
        #         self.hts.connect(port)
        #         self.hts.set_target_temperature(target)
        #         self.hts.enable_control()
        #     except pyvisa.pyvisaIOError:
        #         print('Could not connect to HTS on port ' + port + ' or could not set temperature to ' + target)
        #         return


    @QtCore.pyqtSlot()
    def stop_TEC_temperature_control(self):
        self.tec_enabled = False
        try:
            self.tec.disable_control()
        except pyvisa.pyvisaIOError:
            print('Could not send disable output command to TEC')
        self.tec.close()


    def pulse_and_measure(self, volts, pulse_mag, pulse_width, meas_curr, meas_n, loop_n):
        # see footnote on 6-110 in k2461 manual

        self.dmm.prepare_measure_one()

        start_time = time.time()
        for loop_count in range(loop_n):
            self.mutex.lock()
            if self.is_stopped:
                return
            self.mutex.unlock()
            self.sb.switch(self.assignments["pulse1_assignments"])
            if self.scope_enabled:
                self.scope.single_trig()
            if volts:
                self.pg.prepare_pulsing_voltage(pulse_mag, pulse_width)
            else:
                self.pg.prepare_pulsing_current(pulse_mag, pulse_width)
            self.pg.set_ext_trig()
            time.sleep(500e-3)
            pulse_t = time.time()

            self.pg.send_pulse()

            time.sleep(500e-3)
            self.sb.switch(self.assignments["measure_assignments"])
            self.pg.enable_4_wire_probe(meas_curr)
            time.sleep(500e-3)
            t = np.zeros(meas_n)
            vxx = np.zeros(meas_n)
            vxy = np.zeros(meas_n)
            curr = np.zeros(meas_n)
            if self.tec_enabled:
                tec_data = np.zeros(meas_n)
            for meas_count in tqdm(range(meas_n), desc=f"Loop {loop_count + 1}/{loop_n}, Pulse 1"):
                t[meas_count] = time.time()
                self.pg.trigger_before_fetch()
                self.dmm.trigger()
                vxx[meas_count], curr[meas_count] = self.pg.fetch_one()
                vxy[meas_count] = self.dmm.fetch_one()
                if self.tec_enabled:
                    tec_data[meas_count] = self.tec.get_object_temperature()
            self.pg.disable_probe_current()
            self.pos_data_ready.emit(t - start_time, vxx / curr, vxy / curr)
            if self.scope_enabled:
                scope_data = self.scope.get_data(30001, 60000)
                time_step = float(self.scope.get_time_inc())
                scope_time = np.array(range(0, len(scope_data))) * time_step + pulse_t - start_time

                self.pos_scope_data_ready.emit(scope_time, scope_data / self.reference_resistance)
            if self.tec_enabled:
                self.pos_tec_data_ready.emit(t - start_time, tec_data)

            self.mutex.lock()
            if self.is_stopped:
                return
            self.mutex.unlock()

            self.sb.switch(self.assignments["pulse2_assignments"])
            if self.scope_enabled:
                self.scope.single_trig()
            if volts:
                self.pg.prepare_pulsing_voltage(pulse_mag, pulse_width)
            else:
                self.pg.prepare_pulsing_current(pulse_mag, pulse_width)
            self.pg.set_ext_trig()
            time.sleep(500e-3)
            pulse_t = time.time()

            self.pg.send_pulse()

            time.sleep(500e-3)
            self.sb.switch(self.assignments["measure_assignments"])
            self.pg.enable_4_wire_probe(meas_curr)
            time.sleep(500e-3)

            t = np.zeros(meas_n)
            vxx = np.zeros(meas_n)
            vxy = np.zeros(meas_n)
            curr = np.zeros(meas_n)
            if self.tec_enabled:
                tec_data = np.zeros(meas_n)
            for meas_count in tqdm(range(meas_n), desc=f"Loop {loop_count + 1}/{loop_n}, Pulse 2"):
                t[meas_count] = time.time()
                self.pg.trigger_before_fetch()
                self.dmm.trigger()
                vxx[meas_count], curr[meas_count] = self.pg.fetch_one()
                vxy[meas_count] = self.dmm.fetch_one()
                if self.tec_enabled:
                    tec_data[meas_count] = self.tec.get_object_temperature()
            self.pg.disable_probe_current()
            self.neg_data_ready.emit(t - start_time, vxx / curr, vxy / curr)

            if self.scope_enabled:
                scope_data = self.scope.get_data(30001, 60000)
                time_step = float(self.scope.get_time_inc())
                scope_time = np.array(range(0, len(scope_data))) * time_step + pulse_t - start_time
                self.neg_scope_data_ready.emit(scope_time, scope_data / self.reference_resistance)
            if self.tec_enabled:
                self.neg_tec_data_ready.emit(t - start_time, tec_data)


    def handle_inputs(self, mode, sb_port, bb_port, dmm_port, pulse_mag, pulse_width, meas_curr, meas_n, loop_n,
                      bb_enabled, scope_enabled):
        connection_flag = False
        conversion_flag = False

        if mode == 'Pulse Current':
            pulse_volts = False
        elif mode == 'Pulse Voltage':
            pulse_volts = True
        else:
            print('Pulse mode selection error?')
            pulse_volts = False
            conversion_flag = True

        try:
            sb_port = int(sb_port)
        except ValueError:
            error_sound()
            print('Invalid switchbox port please enter integer value.')
            conversion_flag = True

        if bb_enabled:
            try:
                bb_port = int(bb_port)
            except ValueError:
                error_sound()
                print('Invalid balance box port please enter integer value.')
                conversion_flag = True
            self.bb.enable_all()
            self.bb.set_resistances(self.assignments["resistance_assignments"])

        try:
            dmm_port = int(dmm_port)
        except ValueError:
            error_sound()
            print('Invalid keithley port please enter integer value.')
            conversion_flag = True

        try:
            if pulse_volts:
                pulse_mag = float(pulse_mag)
            else:
                pulse_mag = float(pulse_mag) * 1e-3
        except ValueError:
            error_sound()
            print('Invalid pulse magnitude. Please enter a valid float')
            conversion_flag = True

        try:
            pulse_width = float(pulse_width) * 1e-3
        except ValueError:
            error_sound()
            print('Invalid pulse width. Please enter a valid float')
            conversion_flag = True

        try:
            meas_curr = float(meas_curr) * 1e-6
        except ValueError:
            error_sound()
            print('Invalid probe current. Please enter a valid float')
            conversion_flag = True

        try:
            meas_n = int(meas_n)
        except ValueError:
            error_sound()
            print('Invalid measurement count per loop. Please enter an integer value')
            conversion_flag = True

        try:
            loop_n = int(loop_n)
        except ValueError:
            error_sound()
            print('Invalid number of loops. Please enter an integer value')
            conversion_flag = True

        try:
            self.sb.connect(sb_port)
        except serial.SerialException:
            error_sound()
            print(f"Could not connect to switch box on port COM{sb_port}.")
            connection_flag = True

        if bb_enabled:
            try:
                self.bb.connect(bb_port)
            except serial.SerialException:
                error_sound()
                print(f"Could not connect to balance box on port COM{bb_port}.")
                connection_flag = True

        if scope_enabled & pulse_volts:
            try:
                self.scope.connect()
                self.scope.prepare_for_pulse(pulse_mag, self.reference_resistance, self.two_wire, pulse_width)
                self.scope.set_trig_chan()
                # self.scope.single_trig()
                self.scope_enabled = True
                time.sleep(12)
            except pyvisa.pyvisaIOError:
                error_sound()
                print("Could not connect to RIGOL DS1104Z.")
                connection_flag = True
        else:
            self.scope_enabled = False

        try:
            self.dmm.connect(dmm_port)
        except pyvisa.pyvisaIOError:
            error_sound()
            print(f"Could not connect to Keithley2000 on port COM{dmm_port}.")
            connection_flag = True

        try:
            self.pg.connect()
        except pyvisa.pyvisaIOError:
            error_sound()
            print("Could not connect to keithley 2461.")
            connection_flag = True

        return connection_flag or conversion_flag, pulse_volts, pulse_mag, pulse_width, meas_curr, meas_n, loop_n


# TODO: I need to figure out how to make the tabbing order of the boxes in the gui consistent with vertical placement.
#  Currently it jumps around from top to middle, to bottom and back to 2nd then 4th then the next box.
class MyGUI(QtWidgets.QMainWindow):
    def __init__(self, assignments):
        super(MyGUI, self).__init__()  # Call the inherited classes __init__ method
        self.thread = None
        self.data_collector = None
        self.pos_tec_time = None
        self.switching_dataframe = None
        self.pos_time = None
        self.neg_time = None
        self.pos_rxx = None
        self.neg_rxx = None
        self.pos_rxy = None
        self.neg_rxy = None
        self.scope_enabled = True
        self.pos_scope_time = None
        self.pos_scope_data = None
        self.neg_scope_time = None
        self.neg_scope_data = None
        self.scope_dataframe = None
        self.pos_tec_time = None
        self.pos_tec_data = None
        self.neg_tec_time = None
        self.neg_tec_data = None
        self.temperature_dataframe = None
        self.meta_df = None
        self.rxy_neg_line = None
        self.rxy_pos_line = None
        self.rxy_ax = None
        self.rxx_neg_line = None
        self.rxx_pos_line = None
        self.rxx_ax = None
        self.graph_fig = None
        uic.loadUi('switching_GUI_layoutfile.ui', self)  # Load the .ui file
        self.show()  # Show the GUI
        self.connect_signals()  # this also creates a new thread.
        self.thread.start()  # start the thread created in "connect_signals()"
        self.temp_running = False
        self.assignments = assignments

    def connect_signals(self):
        # Connect gui elements to slots.
        self.pulse_type_combobox.currentTextChanged.connect(self.on_mode_changed)
        self.start_button.clicked.connect(self.on_start)
        self.start_res_button.clicked.connect(self.on_res_measurement)
        self.stop_button.clicked.connect(self.on_stop)
        self.temperature_control_combo.currentIndexChanged.connect(self.on_temp_control_changed)
        self.temperature_control_button.clicked.connect(self.on_temp_start_stop)
        self.thread = QtCore.QThread()
        self.data_collector = DataCollector()
        self.data_collector.moveToThread(self.thread)
        self.data_collector.finished.connect(self.on_loop_over)
        self.data_collector.pos_data_ready.connect(self.on_pos_data_ready)
        self.data_collector.pos_scope_data_ready.connect(self.on_pos_scope_data_ready)
        self.data_collector.pos_tec_data_ready.connect(self.on_pos_tec_data_ready)
        self.data_collector.neg_data_ready.connect(self.on_neg_data_ready)
        self.data_collector.neg_scope_data_ready.connect(self.on_neg_scope_data_ready)
        self.data_collector.neg_tec_data_ready.connect(self.on_neg_tec_data_ready)
        self.data_collector.finished_res_measurement.connect(self.on_res_finished)
        self.data_collector.stable.connect(self.on_stable)
        self.temperature_cont_target_box.setDisabled(True)
        self.temperature_label.setDisabled(True)
        self.temperature_units_label.setDisabled(True)
        self.temperature_control_button.setDisabled(True)
        self.temperature_control_port_box.setDisabled(True)
        self.tc_port_label.setDisabled(True)

    def on_start(self):
        # Reset the data arrays to not append to previous measurements.
        self.switching_dataframe = pd.DataFrame()
        self.pos_time = np.array([])
        self.neg_time = np.array([])
        self.pos_rxx = np.array([])
        self.neg_rxx = np.array([])
        self.pos_rxy = np.array([])
        self.neg_rxy = np.array([])

        self.scope_enabled = False
        if self.scope_checkbox.isChecked():
            self.scope_enabled = True
            self.pos_scope_time = np.array([])
            self.pos_scope_data = np.array([])
            self.neg_scope_time = np.array([])
            self.neg_scope_data = np.array([])
            self.scope_dataframe = pd.DataFrame()

        if self.temp_running:
            self.pos_tec_time = np.array([])
            self.pos_tec_data = np.array([])
            self.neg_tec_time = np.array([])
            self.neg_tec_data = np.array([])
            self.temperature_dataframe = pd.DataFrame()

        self.create_plots()  # make figure axes and so on
        settings_dict = {"assignments": self.assignments,
                         "pulse_type": self.pulse_type_combobox.currentText(),
                         "sb_port": self.sb_port_box.text(),
                         "bb_port": self.bb_port_box.text(),
                         "dmm_port": self.dmm_port_box.text(),
                         "pulse_mag": self.pulse_magnitude_box.text(),
                         "pulse_width": self.pulse_width_box.text(),
                         "probe_current": self.probe_current_box.text(),
                         "measurement_count": self.measurement_count_box.text(),
                         "loop_count": self.loop_count_box.text(),
                         "bb_enabled": self.bb_enable_checkbox.isChecked(),
                         "scope_enabled": self.scope_checkbox.isChecked()}

        self.meta_df = pd.DataFrame({"pulse_type": settings_dict["pulse_type"],
                                     "pulse_mag": settings_dict["pulse_mag"],
                                     "pulse_width": settings_dict["pulse_width"],
                                     "probe_current": settings_dict["probe_current"],
                                     "measurement_count": settings_dict["measurement_count"],
                                     "loop_count": settings_dict["loop_count"],
                                     "target_temp C": self.temperature_cont_target_box.text(),
                                     "dmm_port": settings_dict["dmm_port"],
                                     "sb_port": settings_dict["sb_port"],
                                     "bb_port": settings_dict["bb_port"],
                                     "TC_port": self.temperature_control_port_box.text(),
                                     "bb_enabled": settings_dict["bb_enabled"],
                                     "scope_enabled": settings_dict["scope_enabled"],
                                     "temp_control_type": self.temperature_control_combobox.currentText(),
                                     "pulse1_assignments": assignment_to_str(self.assignments["pulse1_assignments"]),
                                     "pulse2_assignments": assignment_to_str(self.assignments["pulse2_assignments"]),
                                     "measure_assignments": assignment_to_str(self.assignments["measure_assignments"]),
                                     "resistance_assignments": assignment_to_str(
                                         self.assignments["resistance_assignments"]),
                                     "two_wire_assignments": "".join(
                                         [assignment_to_str(x) for x in self.assignments["two_wire_assignments"]]),
                                     "four_wire_assignments": "".join(
                                         [assignment_to_str(x) for x in self.assignments["four_wire_assignments"]]),
                                     'absolute_start_time': time.time()
                                     },
                                    index=[0])
        name = 'temp_data.h5'
        store = pd.HDFStore(name)
        store['meta_data'] = self.meta_df
        print(f'Data saved as {name}')
        store.close()  # save

        # maximum of 9 arguments
        QtCore.QMetaObject.invokeMethod(self.data_collector, 'start_measurement', QtCore.Qt.QueuedConnection,
                                        QtCore.Q_ARG(dict, settings_dict))

        def on_res_measurement(self):

            QtCore.QMetaObject.invokeMethod(self.data_collector, 'resistance_measurement', QtCore.Qt.QueuedConnection,
                                            QtCore.Q_ARG(str, self.pulse_type_combobox.currentText()),
                                            QtCore.Q_ARG(str, self.sb_port_box.text()),
                                            QtCore.Q_ARG(str, self.bb_port_box.text()),
                                            QtCore.Q_ARG(str, self.dmm_port_box.text()),
                                            QtCore.Q_ARG(str, self.pulse_magnitude_box.text()),
                                            QtCore.Q_ARG(str, self.pulse_width_box.text()),
                                            QtCore.Q_ARG(str, self.probe_current_box.text()),
                                            QtCore.Q_ARG(str, self.measurement_count_box.text()),
                                            QtCore.Q_ARG(str, self.loop_count_box.text()),
                                            QtCore.Q_ARG(bool, self.bb_enable_checkbox.isChecked())
                                            )

    def create_plots(self):
        # creates plots and axes objects to be used to plot data.
        # try:
        #     plt.close(self.rxx_fig)
        #     plt.close(self.rxy_fig)
        # except:
        #     print("no plots to close")
        self.graph_fig = plt.figure("Resistance Plots")
        self.rxx_ax = plt.subplot(211)
        self.rxx_ax.clear()
        self.rxx_pos_line, = self.rxx_ax.plot(self.pos_time, self.pos_rxx, 'k.')
        self.rxx_neg_line, = self.rxx_ax.plot(self.neg_time, self.neg_rxx, 'r.')
        # self.rxx_ax.set_xlabel('Time (s)')
        self.rxx_ax.set_ylabel('R_xx (Ohms)')
        self.rxx_ax.ticklabel_format(useOffset=False)

        self.rxy_ax = plt.subplot(212)
        self.rxy_ax.clear()
        self.rxy_pos_line, = self.rxy_ax.plot(self.pos_time, self.pos_rxy, 'k.')
        self.rxy_neg_line, = self.rxy_ax.plot(self.neg_time, self.neg_rxy, 'r.')
        self.rxy_ax.set_xlabel('Time (s)')
        self.rxy_ax.set_ylabel('R_xy (Ohms)')
        self.rxy_ax.ticklabel_format(useOffset=False)
        plt.show(block=False)
        self.refresh_switching_graphs()

        if self.scope_enabled:
            self.scope_fig = plt.figure("scope plots")
            self.scope_ax = plt.axes()
            self.scope_ax.clear()
            self.pos_scope_line, = self.scope_ax.plot(self.pos_scope_time, self.pos_scope_data / 1e3, 'k.')
            self.neg_scope_line, = self.scope_ax.plot(self.neg_scope_time, self.neg_scope_data / 1e3, 'r.')
            self.scope_ax.set_xlabel('Time (s)')
            self.scope_ax.set_ylabel('Pulse Current (mA)')
            self.scope_ax.ticklabel_format(useOffset=False)
            self.refresh_scope_graphs()
            plt.show(block=False)
        if self.temp_running:
            self.tec_fig = plt.figure("tec plots")
            self.tec_ax = plt.axes()
            self.tec_ax.clear()
            self.pos_tec_line, = self.tec_ax.plot(self.pos_tec_time, self.pos_tec_data, 'k.')
            self.neg_tec_line, = self.tec_ax.plot(self.neg_tec_time, self.neg_tec_data, 'r.')
            self.tec_ax.set_xlabel('Time (s)')
            self.tec_ax.set_ylabel('Temperature (°C)')
            self.tec_ax.ticklabel_format(useOffset=False)
            self.refresh_tec_graphs()
            plt.show(block=False)

    def on_mode_changed(self, string):
        # Redraw a few things when changing pulse mode.
        if string == "Pulse Current":
            self.pulse_magnitude_units_label.setText("mA")
            self.pulse_magnitude_box.setText("15")
            print("pulsing_current")
        elif string == "Pulse Voltage":
            self.pulse_magnitude_units_label.setText("V")
            self.pulse_magnitude_box.setText("5")
            print("pulsing_voltage")
        else:
            error_sound()
            print("Something went wrong with the combobox.")

    def on_stop(self):
        # Allows the collector to finish this half-loop (pulse) and for it to offload it's data etc and then to wait.
        mutex = QtCore.QMutex()
        try:
            mutex.lock()
            self.data_collector.is_stopped = True
            mutex.unlock()
        except:
            print("Failed to write due to mutex lock. Trying again.")
            mutex.lock()
            self.data_collector.is_stopped = True
            mutex.unlock()
        print("Stopping")

    def on_loop_over(self):
        print("Finished Loop")
        # when finished is emitted, this will save the data (I hope).
        try:
            # alert_sound()

            prompt_window = QtWidgets.QWidget()

            if QtWidgets.QMessageBox.question(prompt_window, 'Save Data?',
                                              'Would you like to save your data?', QtWidgets.QMessageBox.Yes,
                                              QtWidgets.QMessageBox.No) == QtWidgets.QMessageBox.Yes:
                save_window = QtWidgets.QWidget()
                name, _ = QtWidgets.QFileDialog.getSaveFileName(save_window, "Save Data", "",
                                                                "Text Files (*.txt);; Data Files (*.dat);; All Files (*)")
                if name:  # if a name was entered, don't save otherwise
                    name = name.replace('_scope', '')
                    name = name.replace('_tec', '')
                    name = name.replace('.txt', '')
                    name = name.replace('.hdf', '')
                    name = name.replace('.h5', '')
                    name += '.h5'
                    store = pd.HDFStore(name)
                    store['meta_data'] = self.meta_df
                    store['switching'] = self.switching_dataframe
                    if self.scope_dataframe:
                        store['scope'] = self.scope_dataframe
                    if self.temperature_dataframe:
                        store['temperature'] = self.temperature_dataframe
                    print(f'Data saved as {name}')
                    store.close()  # save
                else:
                    print('No Filename: Data not saved')
            else:
                print('Data not saved')
        except ValueError:
            print("Could not stack. Please manually combine and save pos_temp_data and neg_temp_data "
                  "(and scope data if used).")
        except:
            print("Data not saved, something went wrong! Please check the temp data files")

    def on_pos_data_ready(self, t, rxx, rxy):
        # After pos pulse, plot and store the data then save a backup
        self.pos_time = np.append(self.pos_time, t)
        self.pos_rxx = np.append(self.pos_rxx, rxx)
        self.pos_rxy = np.append(self.pos_rxy, rxy)
        self.rxx_pos_line.set_data(self.pos_time, self.pos_rxx)
        self.rxy_pos_line.set_data(self.pos_time, self.pos_rxy)
        self.refresh_switching_graphs()
        # append the new data to the DF
        self.switching_dataframe = self.switching_dataframe.append(
            pd.DataFrame({'data type': "switching data", 't+': t, 'rxx+': rxx, 'rxy+': rxy}))

        name = 'temp_data.h5'
        store = pd.HDFStore(name)
        store['switching'] = self.switching_dataframe
        print(f'Data saved as {name}')
        store.close()  # save

    def on_pos_scope_data_ready(self, t, current):
        self.pos_scope_time = np.append(self.pos_scope_time, t)
        self.pos_scope_data = np.append(self.pos_scope_data, current)
        self.pos_scope_line.set_data(t, current * 1e3)
        self.refresh_scope_graphs()

        self.scope_dataframe = self.scope_dataframe.append(
            pd.DataFrame({'data type': "scope data", 'scope_t+': t, 'scope_I+': current}))
        name = 'temp_data.h5'
        store = pd.HDFStore(name)
        store['scope'] = self.scope_dataframe
        print(f'Data saved as {name}')
        store.close()  # save

    def on_pos_tec_data_ready(self, t, temperature):
        self.pos_tec_time = np.append(self.pos_tec_time, t)
        self.pos_tec_data = np.append(self.pos_tec_data, temperature)
        self.pos_tec_line.set_data(self.pos_tec_time, self.pos_tec_data)
        self.refresh_tec_graphs()
        self.temperature_dataframe = self.temperature_dataframe.append(
            pd.DataFrame({'t+': t, 'temperature+': temperature}))
        name = 'temp_data.h5'
        store = pd.HDFStore(name)
        store['temperature'] = self.temperature_dataframe
        print(f'Data saved as {name}')
        store.close()

    def on_neg_data_ready(self, t, rxx, rxy):
        # After neg pulse, plot and store the data then save a backup
        self.neg_time = np.append(self.neg_time, t)
        self.neg_rxx = np.append(self.neg_rxx, rxx)
        self.neg_rxy = np.append(self.neg_rxy, rxy)
        self.rxx_neg_line.set_data(self.neg_time, self.neg_rxx)
        self.rxy_neg_line.set_data(self.neg_time, self.neg_rxy)
        self.refresh_switching_graphs()
        self.switching_dataframe = self.switching_dataframe.append(
            pd.DataFrame({'data type': "switching data", 't-': t, 'rxx-': rxx, 'rxy-': rxy}))

        name = 'temp_data.h5'
        store = pd.HDFStore(name)
        store['switching'] = self.switching_dataframe
        print(f'Data saved as {name}')
        store.close()  # save

    def on_neg_scope_data_ready(self, t, current):
        self.neg_scope_time = np.append(self.neg_scope_time, t)
        self.neg_scope_data = np.append(self.neg_scope_data, current)
        self.pos_scope_line.set_data(t, current * 1e3)
        self.refresh_scope_graphs()
        self.scope_dataframe = self.scope_dataframe.append(
            pd.DataFrame({'data type': "scope data", 'scope_t-': t, 'scope_I-': current}))
        name = 'temp_data.h5'
        store = pd.HDFStore(name)
        store['scope_data'] = self.scope_dataframe
        print(f'Data saved as {name}')
        store.close()  # save

    def on_neg_tec_data_ready(self, t, temperature):
        self.neg_tec_time = np.append(self.neg_tec_time, t)
        self.neg_tec_data = np.append(self.neg_tec_data, temperature)
        self.neg_tec_line.set_data(self.neg_tec_time, self.neg_tec_data)
        self.refresh_tec_graphs()
        self.temperature_dataframe = self.temperature_dataframe.append(
            pd.DataFrame({'t-': t, 'temperature-': temperature}))
        name = 'temp_data.h5'
        store = pd.HDFStore(name)
        store['temperature'] = self.temperature_dataframe
        print(f'Data saved as {name}')
        store.close()

    def on_res_finished(self, two_wires, four_wires):
        save_window = QtWidgets.QWidget()
        name, _ = QtWidgets.QFileDialog.getSaveFileName(save_window, "Save Resistance Data", "",
                                                        "Text Files (*.txt);; Data Files (*.dat);; All Files (*)")
        if name:  # if a name was entered, don't save otherwise
            name = name.replace('_2wires', '')
            name = name.replace('_4wires', '')

            name_two_wires = name.replace('.txt', '_2wires.txt')
            np.savetxt(name_two_wires, two_wires, newline='\n', delimiter='\t')  # save
            print(f'Two wires data saved as {name_two_wires}')

            name_four_wires = name.replace('.txt', '_4wires.txt')
            np.savetxt(name_four_wires, four_wires, newline='\n', delimiter='\t')  # save
            print(f'Four wires data saved as {name_four_wires}')
        else:
            print('No Filename: Data not saved')

    def on_temp_control_changed(self, mode):
        if mode == 0:
            self.temperature_cont_target_box.setDisabled(True)
            self.temperature_label.setDisabled(True)
            self.temperature_units_label.setDisabled(True)
            self.temperature_control_button.setDisabled(True)
            self.temperature_control_port_box.setDisabled(True)
            self.tc_port_label.setDisabled(True)
            self.start_button.setDisabled(False)
        else:
            self.temperature_cont_target_box.setDisabled(False)
            self.temperature_label.setDisabled(False)
            self.temperature_units_label.setDisabled(False)
            self.temperature_control_button.setDisabled(False)
            self.temperature_control_port_box.setDisabled(False)
            self.tc_port_label.setDisabled(False)
            self.start_button.setDisabled(True)

    def on_temp_start_stop(self):
        # todo(stu): Need to implement temperature readback in measure loop
        self.temp_running = not self.temp_running
        if self.temp_running:
            self.temperature_control_button.setText("Stop Temperature Control")
            self.start_button.setDisabled(True)
            QtCore.QMetaObject.invokeMethod(self.data_collector, 'start_TEC_temperature_control',
                                            QtCore.Qt.QueuedConnection,
                                            QtCore.Q_ARG(int, self.temperature_control_combo.currentIndex()),
                                            QtCore.Q_ARG(str, self.temperature_control_port_box.text()),
                                            QtCore.Q_ARG(str, self.temperature_cont_target_box.text()))
        else:
            self.temperature_control_button.setText("Start Temperature Control")
            QtCore.QMetaObject.invokeMethod(self.data_collector, 'stop_TEC_temperature_control',
                                            QtCore.Qt.QueuedConnection)
            self.start_button.setDisabled(False)

    def on_stable(self):
        print('Temperature about stable. Verify on controller screen before proceeding.')
        self.start_button.setDisabled(False)

    def refresh_switching_graphs(self):
        # Simply redraw the axes after changing data.
        self.rxx_ax.relim()
        self.rxx_ax.autoscale_view()
        self.rxy_ax.relim()
        self.rxy_ax.autoscale_view()
        self.graph_fig.canvas.draw()

    def refresh_scope_graphs(self):
        self.scope_ax.relim()
        self.scope_ax.autoscale_view()
        self.scope_fig.canvas.draw()

    def refresh_tec_graphs(self):
        self.tec_ax.relim()
        self.tec_ax.autoscale_view()
        self.tec_fig.canvas.draw()


# Starts the application running it's callback loops etc.
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    pulse1_assignments = {"I+": "B", "I-": "F"}  # configuration for a pulse from B to F
    pulse2_assignments = {"I+": "D", "I-": "H"}  # configuration for a pulse from D to H
    measure_assignments = {"I+": "A", "I-": "E", "V1+": "B", "V1-": "D", "V2+": "C", "V2-": "G"}  # here V1 is Vxx

    resistance_assignments = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'E': 0, 'F': 0, 'G': 0, 'H': 0}
    two_wire_assignments = ({"I+": "A", "I-": "E"},
                            {"I+": "B", "I-": "F"},
                            {"I+": "C", "I-": "G"},
                            {"I+": "D", "I-": "H"}
                            )
    four_wire_assignments = ({"I+": "A", "I-": "E", "V1+": "C", "V1-": "G"},
                             {"I+": "B", "I-": "F", "V1+": "D", "V1-": "H"},
                             {"I+": "C", "I-": "G", "V1+": "E", "V1-": "A"},
                             {"I+": "D", "I-": "H", "V1+": "F", "V1-": "B"}
                             )
    assignments = {"pulse1_assignments": pulse1_assignments, "pulse2_assignments": pulse2_assignments,
                   "measure_assignments": measure_assignments, "resistance_assignments": resistance_assignments,
                   "two_wire_assignments": two_wire_assignments, "four_wire_assignments": four_wire_assignments}
    window = MyGUI(assignments)
    window.resize(0, 0)
    app.exec_()
