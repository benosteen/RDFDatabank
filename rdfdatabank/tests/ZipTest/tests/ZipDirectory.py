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

class ZipDirectory(unittest.TestCase):

    def setUp(self):
        self.testpath = "."
        self.testpatt = re.compile("^.*$(?<!\.zip)")
        return

    def tearDown(self):
        return

    def doZip(self):
        files = CollectFiles(self.testpath,self.testpatt)
        z = zipfile.ZipFile('test.zip','w')
        for i in files: 
            n = joinDirName(i[0], i[1])
            z.write(n)
        z.close()
        z = zipfile.ZipFile('test.zip')
        z.testzip()
        z.printdir()
        z.close()

def getTestSuite():
    suite = unittest.TestSuite()
    suite.addTest(ZipDirectory("doZip"))
    return suite

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    runner.run(getTestSuite())
