#!/usr/bin/python2.2
# Startup from single-user installation
# Copyright (C) 2002 John Goerzen
# <jgoerzen@complete.org>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import sys, re, os, pwd, time, base64
from sys import stdin, stdout, argv
import pyme, pyme.core
import GnuPGInterface

args = argv[1:]

if len(args) != 3:
    print """
    USAGE: gruntsend filename delivery dest-filename
    WHERE:
    filename is the local file to send

    delivery is a UUCP path in the form of system!user OR
    an e-mail address in the form of user@system

    dest-filename is the location to place the data in on the remote."""
    sys.exit(1)
    
def copy(infile, outfile):
    while 1:
        data = infile.read(10240)
        if not len(data):
            return
        outfile.write(data)
    

infile = open(args[0])
assert args[1].find('!') != -1, 'e-mail mode not yet supported.'
machine, user = re.search('^(.+)!([^!]+)$', args[1]).groups()
outfile = os.popen("uux -z - '%s!gruntreceive-uucp'" % machine, 'w')

outfile.write(":GRUNT:INSECUREHEADER:FORMAT-1I:\n")
outfile.write(":USER:%s\n" % base64.encodestring(user).strip())
outfile.write(":DATA:\n")
outfile.flush()

gnupg = GnuPGInterface.GnuPG()
gnupg.options.meta_interactive = 1
gnupg.options.armor = 1
process = gnupg.run(['--sign'],
                    create_fhs=['stdin'],
                    attach_fhs={'stdout': outfile})
dataout = process.handles['stdin']
dataout.write(":GRUNT:SECUREHEADER:FORMAT-1S:\n")
dataout.write(":USER:%s\n" % base64.encodestring(user).strip())
dataout.write(":MODE:%s\n" % base64.encodestring('PUT').strip())
dataout.write(":DEST:%s\n" % base64.encodestring(args[2]).strip())
dataout.write(":DATA:\n")
copy(infile, dataout)
infile.close()
dataout.close()
process.wait()
print "Request successfully sent."
