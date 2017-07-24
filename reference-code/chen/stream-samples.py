import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.ptime import time
import serial


maxfilterlen = 32

ser = serial.Serial('/dev/ttyACM0', 115200)

# Keep previous 500 samples to plot
sig = [0]*500
sig_lp = [0]*500
sig_bp = [0]*500

# The plot objects
app = QtGui.QApplication([])
ecgplot = pg.plot()
ecgplot.setWindowTitle('Live ECG')
ecgplot.setTitle('Live ECG')
curve = ecgplot.plot()

# Variable for tracking when the last frame was displayed
last_plot_time = time()
start_time = time()
plotfactor = 3 # only draw the plot every 3 samples collected. Approximately 66 fps.
sampplotcount = 0

while True:
    # Read a sample from the port
    sample = ser.readline().rstrip()
    # Case where an invalid sample is read
    try:
        sample = int(sample)
    except:
        continue
    sampplotcount = sampplotcount + 1

    sig.append(sample)
    sig.pop(0)

    # Apply filters
    sig_lp.append(2*sig_lp[-1] - sig_lp[-2] + sig[-1] - 2*sig[-7] + sig[-13])
    sig_lp.pop(0)
    sig_bp.append(sig_bp[-1] + (-sig_lp[-1] + sig_lp[-33])/32 + sig_lp[-17] - sig_lp[-18] )
    sig_bp.pop(0)

    if sampplotcount == plotfactor:

        curve.setData(sig)
        # redraw plot
        app.processEvents()
        
        sampplotcount = 0
    