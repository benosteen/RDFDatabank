"""
Copyright (c) 2012 University of Oxford

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, --INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
# $Id: TestUtils.py 1047 2009-01-15 14:48:58Z graham $
#
# Support functions for running different test suites
#
# Test suites are selected using a command line argument:
#
# Test classes are:
#   "unit"          These are stand-alone tests that all complete within a few 
#                   seceonds and do not depend on resources external to the 
#                   package being tested, (other than other libraries used).
#   "component"     These are tests that take loonger to run, or depend on 
#                   external resources, (files, etc.) but do not depend on 
#                   external services.
#   "integration"   These are tests that exercise interactions with seperate
#                   services.
#   "pending"       These are tests that have been designed and created, but 
#                   for which the corresponding implementation has not been
#                   completed.
#   "all"           return suite of unit, component and integration tests
#   name            a single named test to be run.
#

import logging
import unittest

def getTestSuite(testclass,testdict,select="unit"):
    """
    Assemble test suite from supplied class, dictionary and selector
    
    testclass   is the test class whose methods are test cases
    testdict    is a dictionary of test cases in named test suite, 
                keyed by "unit", "component", etc., or by a named test.
    select      is the test suite selector:
                "unit"      return suite of unit tests only
                "component" return suite of component tests
                "integrate" return suite of integration tests
                "pending"   return suite of pending tests
                "all"       return suite of unit and component tests
                name        a single named test to be run
    """
    suite = unittest.TestSuite()
    # Named test only
    if select[0:3] not in ["uni","com","all","int","pen"]:
        if not hasattr(testclass, select):
            print "%s: no test named '%s'"%(testclass.__name__, select)
            return None
        suite.addTest(testclass(select))
        return suite
    # Select test classes to include
    if select[0:3] == "uni":
        testclasses = ["unit"]
    elif select[0:3] == "com":
        testclasses = ["component"]
    elif select[0:3] == "int":
        testclasses = ["integration"]
    elif select[0:3] == "pen":
        testclasses = ["pending"]
    elif select[0:3] == "all":
        testclasses = ["unit", "component"]
    else:
        testclasses = ["unit"]
    for c in testclasses:
        for t in testdict.get(c,[]):
            if not hasattr(testclass, t):
                print "%s: in '%s' tests, no test named '%s'"%(testclass.__name__, c, t)
                return None
            suite.addTest(testclass(t))
    return suite

def runTests(logname, getSuite, args):
    """
    Run unit tests based on supplied command line argument values
    
    logname     name for logging output file, if used
    getSuite    function to retrieve test suite, given selector value
    args        command line arguments (or equivalent values)
    """
    sel = "unit"
    vrb = 1
    if len(args) > 1:
        sel = args[1]
    if sel[0:3] in ["uni","com","all","int","pen"]:
        logging.basicConfig(level=logging.WARNING)
        if sel[0:3] in ["com","all"]: vrb = 2
    else:
        # Run single test with elevated logging to file via new handler
        logging.basicConfig(level=logging.DEBUG)
        # Enable debug logging to a file
        fileloghandler = logging.FileHandler(logname,"w")
        fileloghandler.setLevel(logging.DEBUG)
        # Use this formatter for shorter log records
        ###filelogformatter = logging.Formatter('%(levelname)s %(message)s', "%H:%M:%S")
        # Use this formnatter to display timing information:
        filelogformatter = logging.Formatter('%(asctime)s.%(msecs)03d %(levelname)s %(message)s', "%H:%M:%S")
        fileloghandler.setFormatter(filelogformatter)
        logging.getLogger('').addHandler(fileloghandler)
        vrb = 2
    runner = unittest.TextTestRunner(verbosity=vrb)
    tests  = getSuite(select=sel)
    if tests: runner.run(tests)
    return

# End.
