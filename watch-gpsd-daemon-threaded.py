#! /usr/bin/python
#
# basic skeleton from:
#   Dan Mandle http://dan.mandle.me September 2012
#   License: GPL 2.0

import os
import gps
from time import *
import time
import threading

# declare global vars
gpsd = None
gpsd_tpv = None
gpsd_sat = None

os.system('clear') #clear the terminal (optional)

class GpsPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    # connect to gpsd
    self.session = gps.gps("localhost", "2947")
    self.session.stream(gps.WATCH_ENABLE) #  | gps.WATCH_NEWSTYLE
    self.current_value = None
    self.running = True # setting the thread running to true

  def run(self):
    while self.running:
      # this will continue to loop and grab EACH set of gpsd info to clear the buffer
      # next() is blocking, so it will wait for the next report if needed
      self.session.next()
      # export the current report to a global variable
      global gpsd
      gpsd = self.session

if __name__ == '__main__':
  gpsp = GpsPoller() # create the thread
  try:
    gpsp.start() # start it up

    # main infinite loop
    while True:
      #It may take a second or two to get good data
      #print gpsd.fix.latitude,', ',gpsd.fix.longitude,'  Time: ',gpsd.utc

      os.system('clear')

      print
      print ' GPS reading'
      print '----------------------------------------'
      print 'latitude    ' , gpsd.fix.latitude
      print 'longitude   ' , gpsd.fix.longitude
      print 'time utc    ' , gpsd.utc,' + ', gpsd.fix.time
      print 'altitude (m)' , gpsd.fix.altitude
      print 'eps         ' , gpsd.fix.eps
      print 'epx         ' , gpsd.fix.epx
      print 'epv         ' , gpsd.fix.epv
      print 'ept         ' , gpsd.fix.ept
      print 'speed (m/s) ' , gpsd.fix.speed
      print 'climb       ' , gpsd.fix.climb
      print 'track       ' , gpsd.fix.track
      print 'mode        ' , gpsd.fix.mode
      print
      print 'sats        ' , gpsd.satellites

      time.sleep(5) #set to whatever

  # when ctrl+c pressed, or gpsd quits
  except (KeyboardInterrupt, SystemExit, StopIteration):
    print "\nKilling Thread..."
    gpsp.running = False
    gpsp.join() # wait for the thread to finish what it's doing
  print "Done.\nExiting."

