# import tkinter as tk
# from tkinter import filedialog
# import numpy as np
# import matplotlib.pyplot as plt
#
# import os
#
# root = tk.Tk()
# root.withdraw()
# filename = filedialog.askopenfilename(initialdir='../DATA/',
#                                       title='Select a switching file',
#                                       filetypes=(('data files', '*.txt *.dat'), ('all files', '*.*')))
#
# data = np.loadtxt(filename, delimiter='\t')
# # pos_t = data[:, 0]
# # pos_rxx = data[:, 1]
# # pos_rxy = data[:, 2]
# # neg_t = data[:, 3]
# # neg_rxx = data[:, 4]
# # neg_rxy = data[:, 5]
# pos_t = data[:, 0]
# pos_rxx = data[:, 1]
# pos_rxy = data[:, 3]
# neg_t = data[:, 5]
# neg_rxx = data[:, 6]
# neg_rxy = data[:, 8]
#
# graph_fig = plt.figure("Resistance Plots")
# rxx_ax = plt.subplot(211)
# rxx_pos_line, = rxx_ax.plot(pos_t, pos_rxx, 'k.')
# rxx_neg_line, = rxx_ax.plot(neg_t, neg_rxx, 'r.')
# # rxx_ax.set_xlabel('Time (s)')
# rxx_ax.set_ylabel('R_xx (Ohms)')
# rxx_ax.ticklabel_format(useOffset=False)
#
# rxy_ax = plt.subplot(212)
# rxy_pos_line, = rxy_ax.plot(pos_t, pos_rxy, 'k.')
# rxy_neg_line, = rxy_ax.plot(neg_t, neg_rxy, 'r.')
# rxy_ax.set_xlabel('Time (s)')
# rxy_ax.set_ylabel('R_xy (Ohms)')
# rxy_ax.ticklabel_format(useOffset=False)
#
# plt.show()


import tkinter as tk
from tkinter import filedialog
import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

import os

root = tk.Tk()
root.withdraw()
filename = filedialog.askopenfilename(initialdir='../DATA/',
                                      title='Select a switching file',
                                      filetypes=(('data files', '*.txt *.dat'), ('all files', '*.*')))

data = np.loadtxt(filename, delimiter='\t', skiprows=1)

# x = data[:, 0]
# y = data[:,3]
x = data[:, 6] / 15e-3
rxy_sum = data[:, 4] + data[:, 5]
rxy_diff = -data[:, 4] + data[:, 5]

rxx_diff = -data[:, 2] + data[:, 3]
rxx_part = np.mean(data[:, 2]) + np.mean(data[:, 3])
y = signal.savgol_filter(200*rxy_sum/rxx_part, 31, 3)
y = data[:, 2]
y2 = signal.savgol_filter(200*(rxx_diff- np.mean(rxy_diff[0:20]))/rxx_part, 11, 3)
y2 -= np.min(y2)
line, = plt.plot(x, y, 'k.')
# # plt.plot([min(current), max(current)], [min(voltage), max(voltage)])
plt.ticklabel_format(useOffset=False)
plt.xlabel('Field (T)')
plt.ylabel('Sum AMR (%)')
plt.figure()
line2, = plt.plot(x, y2, 'b.')
plt.ylabel('Diff AMR (%)')
plt.xlabel('Field (T)')
plt.grid()
plt.show()
