import numpy as np
import matplotlib.pyplot as plt
import serial
import argparse
import time

ser = serial.Serial('/dev/ttyACM1', 115200)
plt.ion() # set plot to animated


x = list(range(50))
y = [0] * 50

fig = plt.figure()
ax = fig.add_subplot(111)
ax.set_ylim(-1, 1)
line, = ax.plot(x, y, 'r-') # Returns a tuple of line objects, thus the comma

# Only plot the graph every 20 samples collected
plotfactor = 20
samplenum = 0

while True:
    samplenum = samplenum + 1
    sample = ser.readline().rstrip()
    if not sample:
        continue
    y.append((int(sample) - 512) / 512)
    y.pop(0)

    #f = open('savenum','a')
    #f.write(str(int(sample))+"\n")

    #data = ser.readline().rstrip() # read data from serial
    #                               # port and strip line endings
    #
    #if not data:
    #	continue
    #data = int(data)

    #ydata.append(np.random.randint(10))

    #ymin = float(min(ydata))-10
    #ymax = float(max(ydata))+10
    #plt.ylim([ymin,ymax])
    
    #ydata.append(data)
    #ax.set_xlim((x + phase)[0], (x + phase)[-1])
    
    # Only plot every 20 samples
    if samplenum < plotfactor:
    	continue

    line.set_ydata(y)  # update the data

    fig.canvas.draw()

    samplenum = 0