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

# Update parameters when a peak is found
# i is the global index from the start of recording, not 0-500.
def update_running_params(rparams, peaktype, i, peakval):

    # Noise peak
    if peaktype == 'n':
        rparams['noisepeak'] = 0.875*rparams['noisepeak'] + 0.125*peakval
        rparams['recent_noisepeak_inds'].append(i)
        rparams['recent_noisepeak_vals'].append(peakval)
    # Signal peak
    else:
        new_rr = i - rparams['last_qrs_index']
        
        # The most recent 8 rr intervals
        rparams['rr_history_unbound'] = rparams['rr_history_unbound'][1:]+[new_rr]
        rparams['rr_average_unbound'] = np.mean(rparams['rr_history_unbound'])

        # The most recent 8 rr intervals that fall within the acceptable low
        # and high rr interval limits
        if new_rr > rparams['rr_low_limit'] and new_rr < rparams['rr_high_limit']:
            rparams['rr_history_bound'] = rparams['rr_history_bound'][1:]+[new_rr]
            rparams['rr_average_bound'] = np.mean(rparams['rr_history_bound'])
        
            rparams['rr_low_limit'] = 0.92*rparams['rr_average_bound']
            rparams['rr_high_limit'] = 1.16*rparams['rr_average_bound']
            rparams['rr_missed_limit'] =  1.66*rparams['rr_average_bound']

        # Clear the recent noise peaks since last r peak
        rparams['recent_noisepeak_inds'] = []
        rparams['recent_noisepeak_vals'] = []

        rparams['last_qrs_index'] = i
        rparams['heartrate'] = 60*200/rparams['rr_average_bound']

        # Signal peak determined with regular threshold criteria
        if peaktype == 'sr':
            rparams['sigpeak'] = 0.875*rparams['sigpeak'] + 0.125*peakval
        # Signal peak determined with backsearch criteria
        else:
            rparams['sigpeak'] = 0.75*rparams['sigpeak'] + 0.25*peakval

        rparams['thresh'] = 0.25*rparams['sigpeak'] + 0.75*rparams['noisepeak']

    return


def backsearch(rparams, index):
    """
    Search back for recent noise peaks and test for qrs
    using lower thresholds
    
    "If the program does not find a QRS complex in
    the time interval corresponding to 166 percent
    of the current average RR interval, the maximal
    peak deteted in that time interval that lies
    between these two thresholds is considered to be
    a possilbe QRS complex, and the lower of the two
    thresholds is applied"
    """

    # No common peaks since the last r
    if not rparams['recent_noisepeak_inds']
        return

    # Signal index to inspect
    maxpeak_ind = rparams['recent_noisepeak_inds'][np.argmax(rparams['recent_noisepeak_vals'])]

    peakval = rparams['recent_noisepeak_inds'][maxpeak_ind]

    # Thresholds passed, found qrs.
    if peakval > rparams['threshold']/2:
        update_running_params(rparams, 'sb', maxpeak_ind, peakval)

    return

# The radius to search for peaks
peaksearch_radius = 20
# The number of samples the mwi is behind the original signal 
mwidelay = 35

# Running parameters
running_params = {
    'sigpeak':[],
    'noisepeak':[],
    'thresh':[],

    'rr_history_unbound':[],
    'rr_history_bound':[],

    'rr_average_unbound':[],
    'rr_average_bound':[],

    'rr_low_limit':[],
    'rr_high_limit':[],
    'rr_missed_limit':[],

    'recent_noisepeak_inds':[]
    'recent_noisepeak_vals':[],
    'heartrate':[],
    # This value is from the start of recording,
    # confined from 0-500 on the screen.
    'last_qrs_index':[],
}
# The peak detector is delayed by at least (peaksearch_radius + mwidelay) samples.

# --------------------------------------------------------- #

ser = serial.Serial('/dev/ttyACM0', 115200)

# Keep most recent 500 samples to plot
sig = [0]*500
sig_lp = [0]*500
sig_bp = [0]*500
sig_deriv = [0]*500
sig_mwi = [0]*500

# This variable corresponds to the initial unfiltered ecg, used for the final plot.
qrs_locs_sig = []  #[False]*500
# This variable corresponds to the mwi signal from 0 to (end-peaksearch_radius)
# Cannot determine whether last peaksearch_radius samples are peaks and hence qrs.
qrs_locs_mwi = []  #[False]*(500-peaksearch_radius)

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

index = 0

# The initialization learning loop
while running_params['threshold'] == []:
    # Read a sample from the port
    data = ser.readline().rstrip()

    # Case where an invalid sample is read
    try:
        t, sample = data.split()
        sample = int(sample)
    except:
        continue
    sampplotcount = sampplotcount + 1


    # Get new signals and shift indices
    sig.append(sample)
    sig.pop(0)

    # Apply filters
    sig_lp.append(2*sig_lp[-1] - sig_lp[-2] + sig[-1] - 2*sig[-7] + sig[-13])
    sig_lp.pop(0)
    sig_bp.append(sig_bp[-1] + (-sig_lp[-1] + sig_lp[-33])/32 + sig_lp[-17] - sig_lp[-18])
    sig_bp.pop(0)

    # Compute 5 point (squared) derivative of filtered signal
    sig_deriv.append((2*(sig_bp[-1] - sig_bp[-5]) + sig_bp[-2] - sig_bp[-4])**2)
    sig_deriv.pop(0)

    # Obtain mwi signal
    sig_mwi.append(np.sum(sig_deriv[-30])/30)
    sig_mwi.pop(0)

    # Drawing the plot(s)
    if sampplotcount == plotfactor:

        ecgcurve.setData(sig)
        if qrs_locs_sig != []:
            ecgcurve.setData(qrs_locs_sig, sig[qrs_locs_sig])

        bpcurve.setData(sig_bp)
        mwicurve.setData(sig_mwi)

        # redraw plot
        app.processEvents()
        
        sampplotcount = 0
    
    index = index + 1


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


    # Get new signals and shift indices
    sig.append(sample)
    sig.pop(0)

    # Apply filters
    sig_lp.append(2*sig_lp[-1] - sig_lp[-2] + sig[-1] - 2*sig[-7] + sig[-13])
    sig_lp.pop(0)
    sig_bp.append(sig_bp[-1] + (-sig_lp[-1] + sig_lp[-33])/32 + sig_lp[-17] - sig_lp[-18])
    sig_bp.pop(0)

    # Compute 5 point (squared) derivative of filtered signal
    sig_deriv.append((2*(sig_bp[-1] - sig_bp[-5]) + sig_bp[-2] - sig_bp[-4])**2)
    sig_deriv.pop(0)

    # Obtain mwi signal
    sig_mwi.append(np.sum(sig_deriv[-30])/30)
    sig_mwi.pop(0)

    if qrs_locs_mwi != []:
        qrs_locs_mwi = [l-1 for l in qrs_locs_mwi]
        if qrs_locs_mwi[0] == -1:
            qrs_locs_mwi = []


    last_r_distance = index - running_params['last_qrs_index']

    # It has been very long since the last r peak
    # was found. Test recent 'noise' peaks using lower threshold
    if last_r_distance > running_params['rr_missed_limit']:
        backsearch(rparams)
        # Continue with this index whether or not
        # a previous noise peak was marked as qrs
        last_r_distance = index - running_params['last_qrs_index']

    # Check whether the `last - peaksearch_radius` sample of the mwi is a peak
    ispeak = ispeak_radius_end(sig_mwi, peaksearch_radius)

    if ispeak:
        peakval = sig_mwi[-peaksearch_radius]

        # Crosses threshold and is >200ms away
        if sig_mwi > thresh and last_r_distance>40:
            # If the rr interval < 360ms (72 samples), set it as a t wave.
            if last_r_distance < 72:
                update_running_params(running_params, 'n', index, peakval)
            else:
                # Classify as signal peak. Update running parameters
                qrs_locs_mwi.append(500-peaksearch_radius)
                update_running_params(running_params, 'sr', index, peakval)

        # Did not satisfy signal peak criteria.
        # Classify as noise peak
        else:
            update_running_params(running_params, 'n', index, peakval)
    else:
        is_qrs

    if qrs_locs_mwi == []:
        qrs_locs_sig = []
    else:
        qrs_locs_sig = [l- mwidelay for l in qrs_locs_mwi]
        while True:
            if qrs_locs_sig[0] < 0:
                qrs_locs_sig.pop(0)
            else:
                break

    # Drawing the plot(s)
    if sampplotcount == plotfactor:

        ecgcurve.setData(sig)
        if qrs_locs_sig != []:
            ecgcurve.setData(qrs_locs_sig, sig[qrs_locs_sig])

        bpcurve.setData(sig_bp)
        mwicurve.setData(sig_mwi)

        # redraw plot
        app.processEvents()
        
        sampplotcount = 0
    
    index = index + 1