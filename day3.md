# Day 3 - Measuring ECG signals from the Arduino

## Specific Tasks/Questions

- Use the arduino to sample 1 channel ECG at 200Hz.
- Send the results to the computer through a serial port
- Read the values in a python environment
- Save an ecg segment as text
- Read this text file and plot it using a python plotting library

## Resources

- Use BAUDRATE = 115200 in `Serial.begin(BAUDRATE);`
- https://github.com/logston/olimex-ekg-emg
- https://github.com/cx1111/summer-ecg/blob/master/doc/SHIELD-EKG-EMG.pdf
