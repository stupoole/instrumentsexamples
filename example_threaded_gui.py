import time
import numpy as np
import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt


# This class is the worker which will do the data collection and return the data ready for plotting
# This will contain all of the serial commanding and data control.
class Worker(QtCore.QObject):
    finished = QtCore.pyqtSignal()
    dataReady = QtCore.pyqtSignal(np.ndarray)
    stopped = QtCore.pyqtSignal(bool)
    data = np.arange(0, 10000)
    is_stopped = False


    # This method is called by a button "start"
    @QtCore.pyqtSlot()
    def processB(self):
        self.is_stopped = False
        print("Worker.processB()")
        i = 1
        while i < 10 and not self.is_stopped:
            self.data = self.data * 1.1
            time.sleep(5)
            self.dataReady.emit(self.data)
            i += 1
        # self.finished.emit() ## this will call thread.quit if emitted

# This is the function called when the dataRead.emit() is called in processB. This should be a plot window
def onDataReady(array):
    plt.plot(array)
    plt.pause(0.01)

# This starts processB method
def on_start():
    QtCore.QMetaObject.invokeMethod(obj, 'processB', Qt.QueuedConnection)

# This stops the processB method from doing another loop
def on_stop():
    obj.is_stopped = True

# Creates an application. Formality of QT
app = QtWidgets.QApplication(sys.argv)
# make a thread for the serial stuff to occur in
thread = QtCore.QThread()
# create a Qthread worker class which contains all possible methods
obj = Worker()
# Connect the data ready signal to the data onDataReady plotting function
obj.dataReady.connect(onDataReady)
# Move the worker class onto it's own thread
obj.moveToThread(thread)
# Connect the finished signal to a quit function to end the thread. (not used in this example)
obj.finished.connect(thread.quit)

# starts the worker thread.
thread.start()

# Draws a window, displays it, adds 2 buttons with callbacks and then resizes the window.
window = QtWidgets.QWidget()
window.setWindowTitle("Control Window")
window.show()
layout = QtWidgets.QGridLayout(window)
start_button = QtWidgets.QPushButton('Start', window)
stop_button = QtWidgets.QPushButton('Stop', window)
start_button.clicked.connect(on_start)
stop_button.clicked.connect(on_stop)
layout.addWidget(start_button, 0, 0)
layout.addWidget(stop_button, 1, 0)
# window.resize(480, 160)

# Starts the application running it's callback loops etc.
app.exec_()
thread.finished.connect(app.exit)
