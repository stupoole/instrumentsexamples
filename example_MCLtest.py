from mcl import MCL
import time


def print_datareadings(lockinset, datareadings):
    print("Receiving data on set L%i: " % (lockinset + 1), datareadings)


def print_scopereadings(waveformtype, data):
    print("Receiving %s: " % waveformtype, data)


print("Creating MCL object")
mcl = MCL()
print("Finding systems")
systems = mcl.find_systems()
print(systems)
if (len(systems) > 0):
    mcl_ip = str(next(iter(systems)))
else:
    mcl_ip = '192.168.0.11'
mcl_ip = input("Enter MCL IP [%s]: " % mcl_ip) or mcl_ip

# mcl.lidata_data_readings_l1.register_callback(print_datareadings)
# mcl.lidata_data_readings_l1.register_callback(print_datareadings)
# mcl.scope.register_callback(print_scopereadings)
# mcl.fft.register_callback(print_scopereadings)

print("Connect to instrument")
mcl.connect(mcl_ip)

# print("Getting internal voltages")
# print(mcl.config_general_pic_ctrl.val)

# print("Printing installed modules etc.")
# print(mcl.config_general_local_ctrl.val)

print("Frequency 1 is ", mcl.config_frequency_ctrl_f1.val.frequency_hz)
print("Increasing Frequency 1")
mcl.config_frequency_ctrl_f1 = mcl.config_frequency_ctrl_f1.nt(
    frequency_hz=mcl.config_frequency_ctrl_f1.val.frequency_hz + 1,
    rampchanges=False,
    ramptimeconst_s=1
)
print("Frequency 1 is ", mcl.config_frequency_ctrl_f1.val.frequency_hz)

print("Running for 10s")
time.sleep(10)

print("Disconnecting...")
mcl.disconnect()
