import numpy as np
import scipy.signal as scisig
import matplotlib.pyplot as plt
import pdb
plt.ion()

class PanTompkinsSingle(object):
    """
    Class for implementing the Pan-Tompkins
    qrs detection algorithm, using only the MWI
    waveform without matching with the filtered signal.

    """
    def __init__(self, sig=None, fs=None):
        
        if sig.ndim == 2:
            self.sig = sig[:,0]
        self.sig = sig
        self.fs = fs
        
        if sig is not None:
            self.originalsiglen = len(sig)

        # Feature to add
        # "For irregular heart rates, the first threshold
        # of each set is reduced by half so as to increase
        # the detection sensitivity and to avoid missing beats"
        #self.irregular_hr = irregular_hr

    def detect_qrs_static(self):
        """
        Detect all the qrs locations in the static
        signal
        """

        # Resample the signal to 200Hz if necessary
        self.resample()

        # Bandpass filter the signal
        self.bandpass()

        # Calculate the moving wave integration signal
        self.mwi()

        #plt.plot(self.sig)
        #plt.plot(self.sig_F)
        #plt.plot(self.sig_I)

        # Align the filtered and integrated signal with the original
        #self.alignsignals()
        
        # Initialize learning parameters via the two learning phases
        self.learnparams()

        # Recent peaks used in backsearch
        self.recent_noisepeaks = []

        # Loop through every index and detect qrs locations.
        # Start from 200ms after the first qrs detected in the
        # learning phase
        for i in range(self.qrs_inds[0]+41, self.resampledsiglen-20):

            # Number of indices from the previous r peak to this index
            last_r_distance = i - self.qrs_inds[-1]

            # It has been very long since the last r peak
            # was found. Test recent 'noise' peaks using lower threshold
            if last_r_distance > self.rr_missed_limit:

                self.backsearch()
                # Continue with this index whether or not
                # a previous noise peak was marked as qrs
                last_r_distance = i - self.qrs_inds[-1]

            # Determine whether the current index is a peak
            is_peak = ispeak_radius(self.sig_I, self.resampledsiglen, i, 20)
            
            # If a peak is detected classify it as signal or noise
            if is_peak:
                # Crosses threshold and is >200ms away
                if self.sig_I[i] > self.thresh and last_r_distance>40:
                    # If the rr interval < 360ms (72 samples), the peak is checked 
                    # to determine whether it is a T-Wave. This is the final test
                    # to run before the peak can be marked as a qrs complex.
                    if last_r_distance < 72:
                        is_twave = self.istwave(i)
                        
                        if is_twave:
                            # Classified as a t-wave, not a qrs.
                            self.update_peak_params('n', i)
                        else:
                            # Classify as signal peak. Update running parameters
                            self.update_peak_params('sr', i)
                        
                    else:
                        # Classify as signal peak. Update running parameters
                        self.update_peak_params('sr', i)

                # Did not satisfy signal peak criteria.
                # Classify as noise peak
                else:
                    self.update_peak_params('n', i)
        
        # Align the detected qrs complexes back to the original signal
        # to account for filter delay            
        self.alignqrs()

        # Convert the peak indices back to the original fs if necessary
        self.returnresample()
        
        return
    
    def resample(self):
        if self.fs != 200:
            self.sig = scisig.resample(self.sig, int(self.originalsiglen*200/self.fs))

            if self.sig.ndim == 2:
                self.sig = self.sig[:,0]

            self.resampledsiglen = len(self.sig)

        return
    
    # Bandpass filter the signal from 5-15Hz
    def bandpass(self):
        # 15Hz Low Pass Filter
        a_low = [1, -2, 1]
        b_low = np.concatenate(([1], np.zeros(5), [-2], np.zeros(5), [1]))
        sig_low = scisig.lfilter(b_low,        #plt.plot(self.sig_F)
 a_low, self.sig, axis=0)
        

        # 5Hz High Pass Filter - passband gain = 32, delay = 16 samples
        a_high = [1,-1]
        b_high = np.concatenate(([-1/32], np.zeros(15), [1, -1], np.zeros(14), [1/32]))


        self.sig_F = scisig.lfilter(b_high, a_high, sig_low, axis=0)
        

        return

    # Compute the moving wave integration waveform from the filtered signal
    def mwi(self):
        # Compute 5 point derivative
        a_deriv = [1]
        b_deriv = [1/4, 1/8, 0, -1/8, -1/4]

        sig_F_deriv = scisig.lfilter(b_deriv, a_deriv, self.sig_F, axis=0)
        
        # Square the derivative
        sig_F_deriv = np.square(sig_F_deriv)
        
        # Perform moving window integration - 150ms (ie. 30 samples wide for 200Hz)
        a_mwi = [1]
        b_mwi = 30*[1/30]
        
        #print(self.sig.shape)
        #print(self.sig_F.shape)
        #print(sig_F_deriv.shape)


        self.sig_I = scisig.lfilter(b_mwi, a_mwi, sig_F_deriv, axis=0)
        
        return
    
    # Align the filtered and integrated signal with the original
    def alignsignals(self):
        self.sig_F = self.sig_F
        self.sig_I = self.sig_I

        return


    def learnparams(self):
        """
        Initialize detection parameters using the start of the waveforms
        during the two learning phases described.
        
        "Learning phase 1 requires about 2s to initialize
        detection thresholds based upon signal and noise peaks
        detected during the learning process.
        
        Learning phase two requires two heartbeats to initialize
        RR-interval average and RR-interval limit values. 
        
        The subsequent detection phase does the recognition process
        and produces a pulse for each QRS complex"
        
        This code is not detailed in the Pan-Tompkins
        paper. The PT algorithm requires a threshold to
        categorize peaks as signal or noise, but the
        threshold is calculated from noise and signal
        peaks. There is a circular dependency when
        none of the fields are initialized. Therefore this 
        learning phase will detect initial signal peaks using a
        different method, and estimate the threshold using
        those peaks.
        
        This function works as follows:
        - Try to find at least 2 signal peaks (qrs complexes) in the
          first 3 seconds of both signals using simple low order 
          moments. If fewer than 2 signal peaks are detected, shift to the
          next 3 window and try again.
        - Using the classified estimated peaks, threshold is estimated as
          based on the steady state estimate equation: thres = 0.75*noisepeak + 0.25*sigpeak
          using the mean of the noisepeaks and signalpeaks instead of the
          running value.
        - Using the estimated peak locations, the rr parameters are set.
        
        """
        
        # The sample radius when looking for local maxima
        radius = 20
        # The signal start duration (seconds) to use for learning
        learntime = 3
        # The window number to inspect in the signal
        windownum = 0

        while (windownum+1)*learntime*200<self.resampledsiglen:
            wavelearn = self.sig_I[windownum*learntime*200:(windownum+1)*learntime*200]
            
            # Find peaks in the signals
            peakinds = findpeaks_radius(wavelearn, radius)
            peaks = wavelearn[peakinds]
        
            # Classify signal and noise peaks.
            # This is the tricky part

            # Standardize peaks
            peaks = (peaks - np.mean(peaks)) / np.std(peaks)
            
            # Simple cutoff criteria for finding qrs peaks
            sigpeakinds = peakinds[np.where(peaks>=0.5)]
            
            # Noise peaks are the remainders
            noisepeakinds = np.setdiff1d(peakinds, sigpeakinds)

            # Found at least 2 signal peaks >200ms apart, and 1 noise peak
            if len(sigpeakinds)>1 and (sigpeakinds[1]-sigpeakinds[0])>40 and len(noisepeakinds)>0:
                break
            
            # Didn't find 2 satisfactory peaks. Check the next window.
            windownum = windownum+ 1
        
        # Check whether nothing was found

        # Found at least 2 satisfactory qrs peaks. Use them to set parameters.

        # Set running peak estimates to first values
        self.sigpeak = wavelearn[sigpeakinds[0]]
        self.noisepeak = wavelearn[noisepeakinds[0]]
        
        # Use all signal and noise peaks in learning window to estimate threshold
        # Based on steady state equation: thres = 0.75*noisepeak + 0.25*sigpeak
        self.thresh = 0.75*np.mean(wavelearn[noisepeakinds]) + 0.25*np.mean(wavelearn[sigpeakinds])
        # Alternatively, could skip all of that and do something very simple like thresh_F =  max(filtsig[:400])/3
        
        # Set the r-r history using the first r-r interval
        self.rr_history_unbound = [sigpeakinds[1]-sigpeakinds[0]]*8
        self.rr_history_bound = [sigpeakinds[1]-sigpeakinds[0]]*8
        
        self.rr_average_unbound = np.mean(self.rr_history_unbound)
        self.rr_average_bound = np.mean(self.rr_history_bound)
        
        # what is rr_average_unbound ever used for?
        self.rr_low_limit = 0.92*self.rr_average_bound
        self.rr_high_limit = 1.16*self.rr_average_bound
        self.rr_missed_limit =  1.66*self.rr_average_bound

        # The qrs indices detected.
        # Initialize with the first signal peak
        # detected during this learning phase
        self.qrs_inds = [sigpeakinds[0]+windownum*learntime*200]

        return

    # Update parameters when a peak is found
    def update_peak_params(self, peaktype, i):
        
        # Noise peak for integral signal
        if peaktype == 'n':
            self.noisepeak = 0.875*self.noisepeak + 0.125*self.sig_I[i]
            self.recent_noisepeaks.append(i)
        # Signal peak
        else:
            new_rr = i - self.qrs_inds[-1]
            
            # The most recent 8 rr intervals
            self.rr_history_unbound = self.rr_history_unbound[1:]+[new_rr]
            self.rr_average_unbound = np.mean(self.rr_history_unbound)

            # The most recent 8 rr intervals that fall within the acceptable low
            # and high rr interval limits
            if new_rr > self.rr_low_limit and new_rr < self.rr_high_limit:
                self.rr_history_bound = self.rr_history_bound[1:]+[new_rr]
                self.rr_average_bound = np.mean(self.rr_history_bound)
            
                self.rr_low_limit = 0.92*self.rr_average_bound
                self.rr_high_limit = 1.16*self.rr_average_bound
                self.rr_missed_limit =  1.66*self.rr_average_bound

            # Clear the recent noise peaks since last r peak
            self.recent_noisepeaks = []
            self.qrs_inds.append(i)

            # Signal peak determined with regular threshold criteria
            if peaktype == 'sr':
                self.sigpeak = 0.875*self.sigpeak + 0.125*self.sig_I[i]
            # Signal peak determined with backsearch criteria
            else:
                self.sigpeak = 0.75*self.sigpeak + 0.25*self.sig_I[i]

            self.thresh = 0.25*self.sigpeak + 0.75*self.noisepeak
        return


    def backsearch(self):
        """
        Search back for common 2 signal
        peaks and test for qrs using lower thresholds
        
        "If the program does not find a QRS complex in
        the time interval corresponding to 166 percent
        of the current average RR interval, the maximal
        peak deteted in that time interval that lies
        between these two thresholds is considered to be
        a possilbe QRS complex, and the lower of the two
        thresholds is applied"
        
        Interpreting the above 'the maximal peak':
        - A common peak in both sig_F and sig_I.
        - The largest sig_F peak.
        """

        # No common peaks since the last r
        if not self.recent_noisepeaks:
            return

        # Signal index to inspect
        maxpeak_ind = self.recent_noisepeaks[np.argmax(self.recent_noisepeaks)]

        peakval = self.sig_I[maxpeak_ind]

        # Thresholds passed, found qrs.
        if peakval > self.thresh/2:
            self.update_peak_params('sb', maxpeak_ind)

        return


    
    

    def istwave(self, i):
        """
        Determine whether the coinciding peak index happens
        to be a t-wave instead of a qrs complex. 

        "If the maximal slope that occurs during this waveform
        is less than half that of the QRS waveform that preceded
        it, it is identified to be a T wave"

        Compare slopes in filtered signal only
        """

        # Parameter: Checking width of a qrs complex
        # Parameter: Checking width of a t-wave

        # QRS duration between 0.06s and 0.12s
        # Check left half - 0.06s = 12 samples
        qrscheckwidth = 12
        # ST segment between 0.08 and 0.12s.
        # T-wave duration between 0.1 and 0.25s.
        
        # Overall, check 0.12s to the left and of the peak.

        a_deriv = [1]
        b_deriv = [1/4, 1/8, 0, -1/8, -1/4]

        lastqrsind= self.qrs_inds[-1]
        
        qrs_sig_deriv = scisig.lfilter(b_deriv, a_deriv, self.sig_F[lastqrsind-qrscheckwidth:lastqrsind+qrscheckwidth], axis=0)

        checksection_sig_deriv = scisig.lfilter(b_deriv, a_deriv, self.sig_F[i-qrscheckwidth:i+qrscheckwidth], axis=0)

        # Classified as a t-wave if gradient is too low
        if max(checksection_sig_deriv) < 0.5*max(qrs_sig_deriv):
            return True
        else:
            return False

    def alignqrs(self):
        if self.qrs_inds:
            self.qrs_inds = np.array(self.qrs_inds) - 35

    def returnresample(self):
        # Refactor the qrs indices to match the fs of the original signal

        if self.fs!=200:
            self.qrs_inds = self.qrs_inds*self.fs/200
        
        self.qrs_inds = self.qrs_inds.astype('int64')



def pantompkinssingle(sig, fs):
    """
    Pan Tompkins ECG peak detector
    """

    detector = PanTompkinsSingle(sig=sig, fs=fs)

    detector.detect_qrs_static()

    return detector.qrs_inds


# Determine whether the signal contains a peak at index ind.
# Check if it is the max value amoung samples ind-radius to ind+radius
def ispeak_radius(sig, siglen, ind, radius):
    if sig[ind] == max(sig[max(0,ind-radius):min(siglen, ind+radius)]):
        return True
    else:
        return False

# Find all peaks in a signal. Simple algorithm which marks a
# peak if the <radius> samples on its left and right are
# all not bigger than it.
# Faster than calling ispeak_radius for every index.
def findpeaks_radius(sig, radius):
    

    siglen = len(sig)
    peaklocs = []
    
    if sig.ndim ==2:
        sig = sig[:,0]

    # Pad samples at start and end
    sig = np.concatenate((np.ones(radius)*sig[0], sig, np.ones(radius)*sig[-1]))
    
    i=radius
    while i<siglen+radius:
        if sig[i] == max(sig[i-radius:i+radius]):
            peaklocs.append(i)
            i=i+radius
        else:
            i=i+1
        
    peaklocs = np.array(peaklocs)-radius
    return peaklocs

