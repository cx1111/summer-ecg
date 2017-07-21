#!/usr/bin/python

# @Copyright (C) 2017 Augusto Ciuffoletti - All rights reserved
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import serial
import subprocess
import argparse
import time

from subprocess import Popen,PIPE

# Serial communication parameters
BAUDRATE=115200
# Plot parameters
SIZE=1000        # number of samples per plot
REFRESH=20      # number of samples before refresh

smoothed=0
smootheddelta=512
pulse=False
lastpulse=0
pulsePerSecond=0

def analyze(data):
  global smoothed, smootheddelta, pulse, lastpulse, pulsePerSecond
  fields=data.split();
  value=int(fields[1].rstrip())
#  print value
  smoothed = ((smoothed*15)+value)/16
  delta=abs(smoothed-value)
  smootheddelta = ((smootheddelta*15)+delta)/16
  if delta > 200:
#    print fields[0]
    if pulse==False:
      (h,m,s)=fields[0].split(":")
      time=float(s)+(60*(int(m)+(60*int(h))))
      pulsePerSecond=60/(time-lastpulse)
#      print pulsePerSecond
      lastpulse=time
    pulse=True
  else:
    pulse=False
  return (smoothed,pulsePerSecond);

prologue="""
set xtics
set xdata time
set timefmt '%H:%M:%S'
set ytics
set style data lines
set yrange [-1:1]
set grid
set datafile separator ' '
"""

# Processing the commandline arguments 
parser = argparse.ArgumentParser(description='Olimex EKG-EMG visualization')
parser.add_argument(
  '--device', 
  help='Serial device address (e.g. /dev/ttyUSB0)',
  action='store',
  nargs='?',
  default='/dev/ttyUSB0'
  )
parser.add_argument(
  '--username',
  help='User name associated to this ECG (e.g. John)',
  action='store',
  nargs='?',
  default='anonymous'
  )
args = parser.parse_args()


ser = serial.Serial(args.device, BAUDRATE)        # open serial input
data=ser.readline()                               # remove an incomplete line
gnuplot=subprocess.Popen(
  ["gnuplot","-geometry","800x300","-display",":0.0"],
  stdin=PIPE);                                    # open gnuplot process
outFile=open(args.username+"_"+time.strftime("%Y%m%d%H%M")+".dat","w");           # open output file

gnuplot.stdin.write(prologue)                     # set plot properties

buffer=["0:0:0 512"]*SIZE;  # FIFO fixed-size buffer for a single plot image 
count=0;                    # refresh control
while True:
  count=count+1;
  data=ser.readline().rstrip()
  outFile.write(data+"\n")
  buffer.append(data+"\n")
  while len(buffer)>SIZE: # keep buffer length constant
    buffer.pop(0)
  (sv,sd)=analyze(data)
  if (count < REFRESH) | (buffer[0]=="0:0:0 512") : continue # do not refresh image  
#  print data
  rangeMin=buffer[0].split()[0]
  rangeMax=buffer[-1].split()[0]
  gnuplot.stdin.write( "set xrange [\""+rangeMin+"\":\""+rangeMax+"\"]\n")
  gnuplot.stdin.write("set label 1 sprintf(\"user = %s\",\""+args.username+"\") at screen 0.1, screen 0.90\n") 
  gnuplot.stdin.write("set label 2 sprintf(\"ppm = %s\",\""+str(sd)+"\") at screen 0.1, screen 0.85\n")
  gnuplot.stdin.write("plot \"-\" using 1:(($2-512)/512) title 'ecg'\n")
#  gnuplot.stdin.write("plot \"-\" using 1:2 title 'ecg'\n");
  for i, val in enumerate(buffer):
    gnuplot.stdin.write(val)
  gnuplot.stdin.write("e\n")
  count=0
