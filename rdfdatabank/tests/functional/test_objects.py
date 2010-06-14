from rdfdatabank.tests import *

class TestObjectsController(TestController):

    def test_index(self):
        response = self.app.get(url(controller='objects', action='index'))
        # Test response...
