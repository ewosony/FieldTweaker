import unittest
from personal_lite.core import tweak_compatibility
from personal_lite.catalog import TWEAKS

class CompatibilityTests(unittest.TestCase):
    def test_windows_10_rejects_seconds(self):
        t=next(t for t in TWEAKS if t['id']=='seconds')
        self.assertFalse(tweak_compatibility(t,{'supported':True,'build':19045})[0])
    def test_windows_11_accepts_seconds(self):
        t=next(t for t in TWEAKS if t['id']=='seconds')
        self.assertTrue(tweak_compatibility(t,{'supported':True,'build':26100})[0])
    def test_windows_10_rejects_widgets(self):
        t=next(t for t in TWEAKS if t['id']=='widgets')
        self.assertFalse(tweak_compatibility(t,{'supported':True,'build':19045})[0])
    def test_unknown_build_rejected(self):
        t=TWEAKS[0]
        self.assertFalse(tweak_compatibility(t,{'supported':False,'build':0,'reason':'unknown'})[0])

if __name__=='__main__':unittest.main()
