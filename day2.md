# Day 2 - ECG Signal Processing

## Specific Tasks/Questions

- Sampling frequency and signal frequency.
  - Explain the concepts.
  - Plot sine waves with 3 different frequencies [2, 4, 8], sampled at [20, 200] Hz.
  - Plot a sum of three sine waves with frequencies [2, 20, 70] Hz.
- Read in the first channel of all the records in the `day2/data` directory (use the `RECORDS` file). Plot the signals.
- Take a look at the variations within each signal.
- Simple QRS detector
  - Write an amplitude threshold based qrs detector.
  - Test it on several records and plot the results.
  - What causes this approach to fail sometimes?
- Filtering
  - Find a record with high frequency noise. Apply a low pass filter and plot it.
  - Find a record with low frequency noise. Apply a low pass filter and plot it.
  - Apply a bandpass filter on several records. Plot the results. Experiment with the low and high cutoff frequencies.
- Create a more complex QRS detector and test it.

## Resources

- Linear filter: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.lfilter.html
- Butterworth filter design: https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.butter.html

