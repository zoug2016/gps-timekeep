#!/usr/bin/python

import subprocess
import sys

import cgi
import cgitb; cgitb.enable()  # for troubleshooting

print "Content-Type: text/html"     # HTML is following
print                               # blank line, end of headers

# print html header
print """
<html>
<title>ntpi detailed info</title>
<body>
<h1>ntpi detailed info and configuration</h1>
"""

# get the submitted form contents
form = cgi.FieldStorage()

# if rebooting requested, just print a message and exit
if "reboot-button" in form:
    print "<h1>Rebooting now!</h1></body></html>"
    subprocess.Popen(["/sbin/reboot"])
    sys.exit()

# gather system info
ifconfig = subprocess.check_output(["/sbin/ifconfig"], stderr=subprocess.STDOUT)
pstree = subprocess.check_output(["/usr/bin/pstree"], stderr=subprocess.STDOUT)
uptime = subprocess.check_output(["/usr/bin/uptime"], stderr=subprocess.STDOUT)
memory = subprocess.check_output(["/usr/bin/free"], stderr=subprocess.STDOUT)

with open('/sys/class/thermal/thermal_zone0/temp') as f:
    temp = float(f.readline())/1000
with open('/sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq') as f:
    cpuspeed = f.readline().strip()

# print info
print """
 <h3>Uptime and load</h3>
 <blockquote>
   <pre>{uptime}</pre>
 </blockquote>

 <h3>Cpu temperature and speed</h3>
 <blockquote>
   <pre>{temp}'C    {cpuspeed}MHz</pre>
 </blockquote>

 <h3>Network</h3>
 <blockquote>
   <pre>{ifconfig}</pre>
 </blockquote>

 <h3>Memory</h3>
 <blockquote>
   <pre>{memory}</pre>
 </blockquote>

 <h3>Process tree</h3>
 <blockquote>
   <pre>{pstree}</pre>
 </blockquote>
""".format(**locals())

# now editing the configs
print "<h2>Editing the configuration</h2>"

# /etc/network/interfaces editing
print """
<h3>/etc/network/interfaces</h3>
<blockquote>
<p>Edit the network configuration here. Documentation <a href="https://wiki.debian.org/NetworkConfiguration">here</a>.
Supports two IP configurations on one interface, documentation <a href="https://wiki.debian.org/NetworkConfiguration#Multiple_IP_addresses_on_One_Interface">here</a>
  (but not one dhcp and one static, need to be both static or both dhcp).
</p>
<p>
<strong>Warning:</strong> No sanity checks are done. If you mess this up, you won't be able to connect to Pi (you'll need a fresh install or keyboard+monitor)!
"""

INTERFACES_FILE='/etc/network/interfaces'

# pressed 'save-interfaces' button
if "save-interfaces" in form:
    interfaces_submitted_contents = form.getvalue("textarea-interfaces")
    with open(INTERFACES_FILE, 'w') as f:
        f.write(interfaces_submitted_contents)
    print "<p><strong>Message:</strong> file written. Current contents below.</p>"

# read the file contents
with open(INTERFACES_FILE) as f:
    interfaces_contents = f.read()

print """
  <form method="post" action="serverconfig.py">
  <p><textarea name="textarea-interfaces" rows="15" cols="100" style="font-family:monospace;">%s</textarea>
  </p>
  <p><input type="submit" value="Save the file" name="save-interfaces"></p>
  </form>
  </blockquote>
""" % (interfaces_contents)
# cgi.escape(message)

# reboot button
print """
<h3>Reboot the machine</h3>
<blockquote>
<form method="post" action="serverconfig.py">
  <p><input type="submit" value="Reboot!" name="reboot-button"></p>
</form>
</blockquote>
"""

# print the end of html
print "</body></html>"

