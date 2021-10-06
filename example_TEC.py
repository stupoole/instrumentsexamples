import Instruments
import time

tec = Instruments.TEC1089SV()
tec.connect(14)

print(f'object temp = {tec.get_object_temperature()}°C')
print(f'sink temp = {tec.get_sink_temperature()}°C')
print(f'target temp = {tec.get_target_temperature()}°C')
print(f'response = "{tec.set_target_temperature(21)}"')

print("stability: " + tec.get_temp_stability_state())
tec.enable_control()
time.sleep(20)
print("stability: " + tec.get_temp_stability_state())
tec.disable_control()

print(f'object temp = {tec.get_object_temperature()}°C')
print(f'sink temp = {tec.get_sink_temperature()}°C')
