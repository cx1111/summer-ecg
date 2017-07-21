import numpy as np
import pyqtgraph as pg
import serial
import time

ser = serial.Serial('/dev/ttyACM0', 115200)


signal = [0]*500

# The plot object
ecgplot = pg.plot()
ecgplot.setWindowTitle('Live ECG')
curve = ecgplot.plot()

framenum = 0
framefactor = 5

i = 0

while i<999999999999999:
	i = i+1

    data = ser.readline().rstrip()

    if data == b'':
    	continue


    framenum = framenum + 1
    signal.append(int(data))
    signal.pop(0)

    if framenum == framefactor:
    	curve.setData(np.array(signal))
    	framenum = 0


    # Only render every N frames == 200/6 == 33 fps. But this while loop doesn't do shiiiiit.