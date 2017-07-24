# Day 2 - ECG Signal Processing

## Specific Tasks/Questions

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

