#! /usr/bin/python
#
# basic skeleton from:
#   Dan Mandle http://dan.mandle.me September 2012
#   License: GPL 2.0

import gps
import threading
import xmlrpclib
import time
import subprocess
import datetime
import os

# declare global vars and constants
gpsd = None
gps_has_signal = None
ntpd_running = None
rpi_gpio_ntp_running = None

NTPD_NAME = "ntpd"
RPI_GPIO_NTP_NAME = "rpi_gpio_ntp"

HTML_OUTPUT_DIR = "/run/www"
HTML_OUTPUT_FILE = "/index.html"
HTML_TEMPLATE_FILE = "index.template.html"

# auxiliary functions: for supervisord
supervisor_states = {
        0: False,   # stopped
        10: True,   # starting
        20: True,   # running
        30: False,  # backoff (exited too quickly)
        40: False,  # stopping
        100: False, # exited
        200: False, # fatal (could not be started)
        1000: False,# unknown/supervisord programming error
        }
def is_process_running(name):
    return supervisor_states[supervisord.supervisor.getProcessInfo(name)['state']]
def stop_process(name):
    return supervisord.supervisor.stopProcess(name)
def start_process(name):
    return supervisord.supervisor.startProcess(name)

# auxiliary defn: for converting the mode from gpsd into "do we have fix?" boolean
gps_signal_states = {
        0: False, # no mode value yet seen
        1: False, # no fix
        2: True,  # 2D fix
        3: True,  # 3D fix
        }
# preparation: create the dir for html output
if not os.path.exists(HTML_OUTPUT_DIR):
    os.makedirs(HTML_OUTPUT_DIR)

# preparation: read the html template file
fin = open(HTML_TEMPLATE_FILE)
html_template = fin.read()
fin.close()

# auxiliary function: generate a webpage with basic gps/ntpd info
def generate_html_file():
    # gather the info
    gps_info = str(gpsd)
    gps_has_fix = "Yes" if gps_has_signal else "No"
    ntp_info = subprocess.check_output(["ntpq", "-pn"], stderr=subprocess.STDOUT)
    current_time = datetime.datetime.now()
    # write the output file, substituting the variables
    fout = open(HTML_OUTPUT_DIR+HTML_OUTPUT_FILE, "w")
    fout.write(html_template.format(**locals()))
    fout.close()

# connect to supervisor
supervisord = xmlrpclib.Server('http://localhost:9001/RPC2')

# this class does the threaded polling of the gpsd daemon
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
        time.sleep(1) # give gpsd some time to start (in case we start simultaneously)
        gpsp.start() # start it up

        time.sleep(3) # wait for a few reports to come in, to get a possible fix
                      # so that we don't kill ntpd unnecessarily

        # main infinite loop
        while True:
            # does GPS have a fix?
            gps_has_signal = gps_signal_states[gpsd.fix.mode]
            # get the current status of daemons
            ntpd_running = is_process_running(NTPD_NAME)
            rpi_gpio_ntp_running = is_process_running(RPI_GPIO_NTP_NAME)

            # check if the daemons should be running
            if gps_has_signal:
                if not(rpi_gpio_ntp_running):
                    start_process(RPI_GPIO_NTP_NAME)
                if not(ntpd_running):
                    start_process(NTPD_NAME)
            else:
                if rpi_gpio_ntp_running:
                    stop_process(RPI_GPIO_NTP_NAME)
                if ntpd_running:
                    stop_process(NTPD_NAME)

            generate_html_file()

            #os.system('clear')
            #print gpsd

            # wait for X seconds until the next cycle
            time.sleep(2)

    # when ctrl+c pressed, or gpsd quits
    except (KeyboardInterrupt, SystemExit, StopIteration):
        print "\nKilling Thread..."
        gpsp.running = False
        gpsp.join() # wait for the thread to finish what it's doing
    print "Done.\nExiting."

