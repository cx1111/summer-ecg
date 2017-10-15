import serial
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.ptime import time as ptime
import numpy as np
import os


def findqrs(sig, thresh = 600, peakradius=5):
    
    #crossups=[]*500
    #crossdowns=[]*500
    qrs_locs=[]
    
    for i in range(peakradius, len(sig)-peakradius):
        if sig[i] > thresh and sig[i] == max(sig[i-peakradius:i+peakradius]):
            if qrs_locs == [] or (i - qrs_locs[-1]) > 66: 
                qrs_locs.append(i)

    # for i in range(1,data):
    #     if sig[i] >= thresh and sig[i-1] <= thresh:
    #         crossups.append(i)
            
    #     if sig[i] <= thresh and sig[i-1] >= thresh:
    #         crossdowns.append(i)
            
    #     #print("crossups" + str(crossups))
    #     #print("crossdowns" + str(crossdowns))
    #     if len(crossdowns) >= len(crossups):
    #         crossups.append(None)

    #     if sig[i] > thresh:
    #         crossups.append(i)
    #     elif sig[i] < thresh:
    #         crossdowns.append(i)
    #     if crossdowns == [] and crossups == [0]:
    #         crossdowns = 0
    #     for crossnum in range(len(crossups)) or range(len(crossdowns)):
        
    #         highsegment = sig[crossups[crossnum]:crossdowns[crossnum]]
    #         print(highsegment)
    #         qrs = np.where(highsegment == max(highsegment))[0][0]
    #         print(highsegment)
    #         qrs_locs.append(qrs+tuple(crossups[crossnum]))
        
    return qrs_locs
