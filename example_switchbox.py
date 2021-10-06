import numpy as np
import time
# import tkinter as tk
# import tkinter.messagebox as mb
# from tkinter import filedialog as dialog
import matplotlib
import instruments

switchbox = instruments.SwitchBox()
#dual arm pulsing
pulse1_assignments = {"I+": "BD", "I-": "FH"}
# single arm pulsing
pulse2_assignments = {"I+": "D", "I-": "H"}
# measuring with two different kiethley connectors to one pin
measure_assignments = {"I+": "A", "I-": "E", "V1+": "A", "V1-": "E", "V2+": "C", "V2-": "G"}

switchbox.connect(4)

# switch between example configs every second. Listen for clicking.
switchbox.switch(pulse1_assignments)
time.sleep(1)
switchbox.switch(measure_assignments)
time.sleep(1)
switchbox.switch(pulse2_assignments)
time.sleep(1)
switchbox.switch(pulse2_assignments)
time.sleep(1)
switchbox.reset_all()
