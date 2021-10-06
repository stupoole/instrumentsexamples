import Instruments
import time

lockinA = Instruments.Model_5210()
lockinB = Instruments.Model_5210()
ac = Instruments.K6221()

lockinA.connect(6)
lockinB.connect(9)
ac.connect_RS232(10)

lockinA.set_sensitivity(3)
lockinA.set_time_constant(1e-1)
ac.sine_wave(1e3, 1)
ac.wave_output_on()
time.sleep(1)
lockinA.auto_phase()
lockinB.auto_phase()
time.sleep(1)
print(lockinA.get_xy())
print(lockinB.get_xy())
ac.wave_output_off()
lockinA.close()
lockinB.close()

ac.close()



import Instruments
lockinA = Instruments.Model_5210()
lockinA.connect(6)


time.sleep(0.4)
lockinA.get_x_rapid()
