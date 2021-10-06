import time
import instruments

# Change the port and run this and listen for clicking. the 5s delays are to test the resistances
resistances = {"A": 50, "B": 50, "C": 50, "D": 50, "E": 50, "F": 50, "G": 50, "H": 50}
balance_box = instruments.BalanceBox()
balance_box.connect(5)

#  Disable all channels to close all connections
balance_box.disable_all()
time.sleep(5)
# Enable all channels
balance_box.enable_all()
time.sleep(5)
# set all the resistances to 50 ohms
balance_box.set_resistances(resistances)
time.sleep(5)
# Set them all to ~0.3 ohms
balance_box.reset_resistances()
time.sleep(5)
