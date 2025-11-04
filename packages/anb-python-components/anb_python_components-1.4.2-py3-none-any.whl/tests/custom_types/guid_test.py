# tests/custom_types/guid_test.py

import unittest

from anb_python_components.custom_types.guid import GUID

class GUIDTest(unittest.TestCase):
    def test_init (self):
        guid = GUID('12345678-1234-1234-1234-123456789012', )
        
        self.assertEqual(str(guid), '12345678-1234-1234-1234-123456789012')

if __name__ == '__main__':
    unittest.main()