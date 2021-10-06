import Instruments
import numpy as np
import time
import matplotlib.pyplot as plt


tec = Instruments.TEC1089SV()

print(tec.connect(14))
tec.set_target_temperature(21)
n = 25
temp = np.zeros(n)
t = np.zeros(n)
start_time = time.time()
for i in range(n):
    x = tec.get_object_temperature()
    print(x)
    temp[i] = x
    t[i] = time.time() - start_time
    # time.sleep(0.1)

plt.plot(t, temp)
plt.show()