#! /usr/bin/python
#
# basic skeleton from:
#   Dan Mandle http://dan.mandle.me September 2012
#   License: GPL 2.0

import os
import gps
import threading
import xmlrpclib
from time import *
import time

# declare global vars
gpsd = None

# connect to supervisor
supervisord = xmlrpclib.Server('http://localhost:9001/RPC2')

os.system('clear') #clear the terminal (optional)

class GpsPoller(threading.Thread):
  def __init__(self):
    threading.Thread.__init__(self)
    # connect to gpsd
    self.session = gps.gps("localhost", "2947")
    self.session.stream(gps.WATCH_ENABLE | gps.WATCH_NEWSTYLE)
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
      # note to self: does not export individual reports;
      # the 'session' holds the "current" info
      # the individual reports are return values to the
      # self.session.next() call
      # --- to print all the callable methods of an object:
      #print [method for method in dir(gpsd) if callable(getattr(gpsd, method))]
      # --- to print all the properties of an object:
      #print dir(gpsd.fix)

if __name__ == '__main__':
  gpsp = GpsPoller() # create the thread
  try:
    gpsp.start() # start it up

    # main infinite loop
    while True:
      #It may take a second or two to get good data
      #print gpsd.fix.latitude,', ',gpsd.fix.longitude,'  Time: ',gpsd.utc

      os.system('clear')

      print gpsd

      #print gpsd.fix.mode

      time.sleep(3) #set to whatever

  # when ctrl+c pressed, or gpsd quits
  except (KeyboardInterrupt, SystemExit, StopIteration):
    print "\nKilling Thread..."
    gpsp.running = False
    gpsp.join() # wait for the thread to finish what it's doing
  print "Done.\nExiting."

