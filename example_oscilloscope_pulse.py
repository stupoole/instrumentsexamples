import Instruments
import time
import matplotlib.pyplot as plt
import numpy as np


pg = Instruments.K2461()
pg.connect()
v_pulse = 5
scope = Instruments.DS1104()
scope.connect()
scope.prepare_for_pulse(v_pulse)
scope.set_trig_chan(3)
scope.single_trig()

time.sleep(12)

pg.prepare_pulsing_voltage(v_pulse, 500e-6)
print("pulse now")
pg.send_pulse()

time.sleep(0.2)
n = 125000/2
s = 15
data = scope.get_data(15001, 30000)
time_step = float(scope.get_time_inc())
time = np.array(range(0, len(data))) * time_step
res = 2973.5
plt.figure()
plt.plot(time, data/res)
plt.xlabel('time (s)')
plt.ylabel('current (mA)')

plt.show()

