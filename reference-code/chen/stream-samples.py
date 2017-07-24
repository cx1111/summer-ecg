import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.ptime import time as ptime
import serial


# --------------- Peak Detector Content ------------------ #

# Checks whether the `last - radius` sample of a signal is the largest
# value within `radius` samples left and right of it
def ispeak_radius_end(sig, radius):
    if sig[-radius-1] == max(sig[-2*radius-1:]):
        return True
    else:
        return False

# The radius to search for peaks
peaksearch_radius = 20
# The number of samples the mwi is behind the original signal 
mwidelay = 35

thresh = 0

# --------------------------------------------------------- #




ser = serial.Serial('/dev/ttyACM0', 115200)

# Keep most recent 500 samples to plot
sig = [0]*500
sig_lp = [0]*500
sig_bp = [0]*500
sig_deriv = [0]*500
sig_mwi = [0]*500

is_qrs = [False]*(500+mwidelay)

# The plot objects
app = QtGui.QApplication([])
ecgplot = pg.plot()
ecgplot.setWindowTitle('Live ECG')
ecgplot.setTitle('Live ECG')
#ecgplot.setYRange (0, 530)
ecgplot.setYRange (-1500, 2200)
ecgcurve = ecgplot.plot()

bpplot = pg.plot()
bpplot.setWindowTitle('Bandpass Filtered Signal')
bpplot.setTitle('Bandpass Filtered Signal')
#mwiplot.setYRange (0, 600)
bpcurve = bpplot.plot()

mwiplot = pg.plot()
mwiplot.setWindowTitle('MWI Signal')
mwiplot.setTitle('MWI Signal')
#mwiplot.setYRange (0, 600)
mwicurve = mwiplot.plot()

# Variable for tracking when the last frame was displayed
plotfactor = 3 # only draw the plot every 3 samples collected. Approximately 66 fps.
sampplotcount = 0


# The steady state loop
while True:
    # Read a sample from the port
    data = ser.readline().rstrip()

    # Case where an invalid sample is read
    try:
        t, sample = data.split()
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

    # Compute 5 point (squared) derivative of filtered signal
    sig_deriv.append((2*(sig_bp[-1] - sig_bp[-5]) + sig_bp[-2] - sig_bp[-4])**2)
    sig_deriv.pop(0)

    # Obtain mwi signal
    sig_mwi.append(np.sum(sig_deriv[-30])/30)
    sig_mwi.pop(0)

    # Search for qrs complex

    # Check whether the `last - peaksearch_radius` sample is a peak
    ispeak = ispeak_radius_end(sig_mwi, peaksearch_radius)



    # Drawing the plot(s)
    if sampplotcount == plotfactor:

        ecgcurve.setData(sig)
        bpcurve.setData(sig_bp)
        mwicurve.setData(sig_mwi)

        # redraw plot
        app.processEvents()
        
        sampplotcount = 0
    