# $Id: TestAll.py 1047 2009-01-15 14:48:58Z graham $
#
# Unit testing for WebBrick library functions (Functions.py)
# See http://pyunit.sourceforge.net/pyunit.html
#

import sys, unittest, logging, zipfile, re
from os.path import normpath

# Add main library directory to python path
sys.path.append("../..")
from MiscLib.ScanFiles import *

def matchfile(filnam):
    rexp = re.compile("^.*$(?<!\.zip)")
    return rexp.match(filnam)

print "foo.txt..."
assert matchfile("foo.txt"), "foo.txt"
print "foo.zip..."
assert not matchfile("foo.zip"), "foo.zip"
print "foo.zip.txt..."
assert matchfile("foo.zip.txt"), "foo.zip.txt"


