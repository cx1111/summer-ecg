import serial
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.ptime import time as ptime
import numpy as np
import os
from qrsattempt2 import findqrs
import sys
from pygame import mixer
from pygame.locals import * 

thresh = 800
peakradius = 5
isqrs = False

hr = 0
ser = serial.Serial('/dev/ttyACM1', 115200)

app = QtGui.QApplication([])
ecgplot = pg.plot()
ecgplot.setWindowTitle('Live ECG')
ecgplot.setTitle('Live ECG')
ecgplot.setYRange (0, 1000)
ecgplot.setXRange (0, 500)
ecgcurve = ecgplot.plot()
#ecgplot.addLegend('Raw ECG')
#text = pg.TextItem(html='<div style="text-align: center"><span style="color: #FFF;">Sampnum</span><br><span style="color: #FF1; font-size: 16pt;"></span></div>', anchor=(-0.3,0.5), angle=360, border='w', fill=(0, 0, 255, 50))
#text2 = pg.TextItem(html='<div style="text-align: center"><span style="color: #FFF;"></span><br><span style="color: #FF1; font-size: 16pt;"></span></div>', anchor=(-0.3,0.5), angle=360, border='w', fill=(255, 0, 0, 50))
text = pg.TextItem(anchor=(-0.3,0.5), angle=360, border='w', fill=(0, 0, 255, 50))
text2 = pg.TextItem(anchor=(-0.3,0.5), angle=360, border='w', fill=(255, 0, 0, 50))

ecgplot.addItem(text)
ecgplot.addItem(text2)

text.setPos(0, 150)
text2.setPos(0, 0)

mixer.init() #you must initialize the mixer
alert=mixer.Sound('/home/nathan/Downloads/beep-07.wav')
alert2 = mixer.Sound('/home/nathan/Downloads/beep-01a.wav')
alert3 = mixer.Sound('/home/nathan/Downloads/beep-05.wav')
DeathBuzzer = mixer.Sound('/home/nathan/Downloads/beep-11.wav')
#ecgplot2 = pg.plot()
#ecgplot2.setTitle('Second Live ECG')
ecgcurve1 = ecgplot.plot()
#ecgcurve3 = ecgplot.plot()
#ecgcurve4 = ecgplot.plot()


Gateway = [0]*500
isqrslst = []
plotyn = 0



# Stores the last 5 rr intervals
qrs_loc_history = []
# Global last qrs location, indexed by sampnum.
last_qrs_loc = None
# Number of samples collected since start of program
sampnum = 0

hr = None
hs = False

while True:
    
    try:
        data = int(ser.readline().rstrip())
    except:
        continue

    Gateway.append(data)
    Gateway.pop(0)  

    if plotyn == 6:
        # ecgplot.setTitle('changing number' + str(sampnum, "sampnum"))
        # pg.addLegend()
        
        #qrs_locs = findqrs(Gateway)
        #plotsigandqrs(Gateway, qrs_locs)
        ecgcurve.setData(Gateway)

        
        # text = pg.TextItem((html='<div style="text-align: center"><span style="color: #FFF;">This is the</span><br><span style="color: #FF0; font-size: 16pt;">PEAK</span></div>', anchor=(-0.3,0.5), angle=45, border='w', fill=(0, 0, 255, 100)))
        # plt.addItem(text)
        # text.setPos(0, y.max()
        #ecgcurve2.setData(Gateway)
        #print(isqrslst)
        
        #ecgcurve2.setData(isqrslst, np.array(Gateway)[isqrslst], pen=pg.mkPen(color='g', style=QtCore.Qt.DotLine))
        #print(isqrslst)
        #app.processEvents()
        
        plotyn = 0
        
        qrs_locs = findqrs(Gateway, thresh, peakradius)

        if qrs_locs != []:
            global_qrs_locs = [q + sampnum for q in qrs_locs]
            
            if last_qrs_loc != global_qrs_locs[-1]:
                last_qrs_loc = global_qrs_locs[-1]
                alert.play()
                qrs_loc_history.append(global_qrs_locs[-1])
            
                if len(qrs_loc_history) == 6:
                    
                    qrs_loc_history.pop(0)
                    # T = sampnum/60
                    # rr_history = T/5    
                    rr_avg = np.average(np.diff(qrs_loc_history))
                    hr = 12000/rr_avg

        # It has been too long since a beat. Reset qrs history and make hr=0.
        if last_qrs_loc is not None and sampnum - last_qrs_loc >= 600:
            qrs_loc_history = []
            last_qrs_loc = None
            hr = 0
        
        if hr is None or len(qrs_loc_history)>0 and len(qrs_loc_history)<5:
            text.setText("Heart Rate: <configuring...>")
            text2.setText('Status: Fine')
        elif hr == 0:
            DeathBuzzer.play()
            text.setText("Heart Rate: "+str(hr)+" bpm")
            text2.setText("<WARNING! Heart stopped. Check patient for issues>")
        else:
            text.setText("Heart Rate: "+str(hr)+" bpm")
            text2.setText('Status: Fine')
            if hr <= 30:
                text2.setText("<WARNING! Heart rate too Low!!>")
                alert2.play()
            elif hr >= 180:
                text2.setText("<WARNING! Heart rate too High!!>")
                alert3.play()
        
        ecgcurve1.setData(qrs_locs,np.array(Gateway)[qrs_locs], pen=None, symbol='o')
        
        
        app.processEvents()

    plotyn = plotyn + 1

    sampnum +=1