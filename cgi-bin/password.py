#!/usr/bin/python
# -*- coding: UTF-8 -*-

import subprocess
import sys
import os

import cgi
import cgitb; cgitb.enable()  # for troubleshooting

# constants
SUPERVISOR_CONF = "/etc/supervisor/conf.d/daemons.conf"
AUTH_FILE = "/opt/gps-timekeep/auth"

PERMISSIONS_S = """
<h3>Can't change password via web interface: permissions problem</h3>
<h4>Change password "manually"</h4>
<ul>
<li>SSH into the machine.</li>
<li>Change name:pass by editing two files:
  <ul>
  <li><pre>/etc/supervisor/conf.d/daemons.conf</pre></li>
  <li><pre>/opt/gps-timekeep/auth</pre></li>
  </ul>
<li>Passwords need to match!!</li>
<li>Restart the machine (otherwise unexpected stuff can occur).</li>
</ul>
<h4>Alternatively, fix the permissions</h4>
The two files above need to be write-accessible by the lighttpd process, so you can for instance (after SSHing into the machine):
<blockquote><pre>
sudo chgrp www-data /opt/gps-timekeep/auth
sudo chmod g+w /opt/gps-timekeep/auth
</pre></blockquote>
and the same with the other file.
</body></html>
"""

print "Content-Type: text/html;charset=utf-8"     # HTML is following
print                               # blank line, end of headers

# print html header
print """
<html>
<title>ntpi: change password</title>
<body>
<h1>ntpi: change password</h1>
"""

# get the submitted form contents
form = cgi.FieldStorage()

# if rebooting requested, just print a message and exit
if "reboot-button" in form:
    print "<h1>Rebooting now!</h1></body></html>"
    subprocess.Popen(["/sbin/reboot"])
    sys.exit()

# check if the appropriate files are writable
if (not os.access(SUPERVISOR_CONF, os.W_OK | os.R_OK)) or (not os.access(AUTH_FILE, os.W_OK | os.R_OK)):
    print PERMISSIONS_S
    sys.exit()

# change of password requested
if "submit-button" in form:
   username = form.getvalue("username")
   password = form.getvalue("password")
   with open(AUTH_FILE, "w") as f:
       f.write(username+":"+password+"\n")
   with open(SUPERVISOR_CONF) as f:
       lines = f.readlines()
   with open(SUPERVISOR_CONF, "w") as f:
       for line in lines:
           if line.startswith("username "):
               f.write("username = " + username + "\n")
           elif line.startswith("password "):
               f.write("password = " + password + "\n")
           else:
               f.write(line)
   print """
        <form method="post" action="password.py">
        </p><strong>Message:</strong> Username and password changed. You should 
            <input type="submit" value="Reboot!" name="reboot-button"> now.
        </form></p>
        """

# read username and password
username = "some error"
password = "has occured"
with open(AUTH_FILE) as f:
    username, password = f.readline().strip().split(':')

# print the form
print """
<blockquote>
<form method="post" action="password.py">
<p>
Username: <input type="text" name="username" value="%s"/><br />
Password: <input type="text" name="password" value="%s"/><br />
<input type="submit" value="Submit" name="submit-button"></p>
</form>
Note: No sanity checking is done, so be careful!
</blockquote>
<p>
<a href="/cgi-bin/serverconfig.py">Go back.</a>
</p>
</body></html>
""" % (username, password)

