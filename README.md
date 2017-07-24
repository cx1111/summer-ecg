# Summer ECG Project 2017

Exploration of ECG signals. 

# Tasks

## Software Prerequisites

1. Install the C-Python interpreter (what is commonly referred to as 'python').
2. Install pip, the python package installer.
3. Install the wfdb-python package by running: `pip install wfdb`. See the project home of the package in the *resources* section below.

## Task 1 - Initial Visualization

1. Load ECG signals from PhysioNet's NSRDB or MITDB into python environment. You will load signals using the `rdsamp` function from the wfdb-python package. Visualize the signals.
2. Load the corresponding annotation files from PhysioNet into python environment. Plot the qrs locations on top of the signals.
3. Calculate r-r intervals and instantaneous heart rate. Plot these values with the qrs locations on top of the signals.

## Task 2 - QRS Detection

1. Create a simple amplitude threshold based QRS detector. Test on:
  - A clean signal
  - A noisy signal
2. Filter a noisy ecg signal. Test the previous amplitude based QRS dectector.
3. Run an existing complicated QRS detector (Pan Tompkins) on a clean and noisy signal. 
  - Compare the results of this detector with your simple filter+amplitude detector.
  - Explain the working steps of the Pan-Tompkins algorithm

## Task 3 - Arduino

1. Assemble the ECG device and use it to measure your ECG. Stream the signal to your laptop and view the streamed signal in a viewer.
  - Move around
  - Hold your breath
  - Try the Valsalva maneuver
2. Save an ECG segment in a file.
2. Load your saved ECG signal into the python environment. Run a QRS detector, and display the signal and beat locations.

## Task 4 - Live ECG Display

Help build the live ECG display which has the following features:
- Displays the live ECG stream collected from the Arduino.
- Detects and displays QRS peaks. Makes a sound when a QRS complex is detected.
- Calculates and displays instantaneous heart rate.
- Sounds an alarm when heart rate crosses a threshold.

# Resources

## ECG

- The project page of the wfdb-python package: https://github.com/MIT-LCP/wfdb-python
- The MIT BIH Arrhythmia Database: https://physionet.org/physiobank/database/mitdb/
- The Normal Sinus Rhythm Database: https://physionet.org/physiobank/database/nsrdb/

## Arduino

- https://www.arduino.cc/en/Guide/Linux/
- https://www.arduino.cc/en/Guide/HomePage
- https://www.arduino.cc/en/Tutorial/HomePage
- https://www.arduino.cc/en/Reference/HomePage

## Python Packages

- pyqtgraph documentation: http://www.pyqtgraph.org/documentation/

