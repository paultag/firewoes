import os
import sys
import unittest
#import tempfile
import json
from glob import glob

os.environ["FIREWOSE_TESTING"] = "testing"
from app import app
os.environ["FIREWOSE_TESTING"] = ""

parentdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0,parentdir)
from lib import firehose_orm
from bin import fill_db


class FirewoseTestCase(unittest.TestCase):
    ClassIsSetup = False
    
    def setUp(self):
        # from http://stezz.blogspot.fr
        # /2011/04/calling-only-once-setup-in-unittest-in.html
        
        # If it was not setup yet, do it
        if not self.ClassIsSetup:
            print "Initializing testing environment"
            # run the real setup
            self.setupClass()
            # remember that it was setup already
            self.__class__.ClassIsSetup = True
    
    def setupClass(self):
        
        # we fill firewose_test with our testing data:
        print("Filling db...")
        xml_files = glob("tests/*.xml")
        #fill_db.read_and_create(app.config['DATABASE_URI'],
        #                        xml_files, drop=True, echo=False)

        self.__class__.app = app.test_client()
        
    def tearDown(self):
        pass
        
    def test_static_pages(self):
        rv = self.app.get('/')
        assert 'Firewose' in rv.data

    def test_packages_suggestions(self):
        rv = json.loads(self.app.get('/api/search/?sut_name=pyth').data)
        assert rv['packages_suggestions'][0]["name"] == "python-ethtool"
        
    def test_search_list(self):
        rv = json.loads(self.app.get('/api/search/?sut_name=python-ethtool&location_file=python-ethtool%2Fethtool.c').data)
        assert rv["results"][0]["sut_name"] == "python-ethtool"
        assert rv["results"][0]["location_file"] == "python-ethtool/ethtool.c"
        assert rv["page"] == 1
        
    def test_drilldown_menu(self):
        rv = json.loads(self.app.get('/api/search/?sut_name=python-ethtool&location_file=python-ethtool%2Fethtool.c').data)
        
        assert rv["menu"][2]["active"] is True
        assert rv["menu"][2]["value"] == "python-ethtool"
        assert rv["menu"][2]["remove_filter"].keys() == ["location_file"]
        
        assert rv["menu"][0]["active"] is False
        assert rv["menu"][0]["items"][0]["add_filter"].keys() == [
            "sut_name", "result_type", "location_file"]
        assert rv["menu"][0]["items"][0]["name"] == "issue"

if __name__ == '__main__':
    unittest.main()