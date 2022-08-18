import pycape
from pycape.cape import _convert_to_function_ref, _generate_nonce
import unittest

class Test(unittest.TestCase):
    def test_convert_to_function_ref(self):
        CAPE_FUNCTION_ID = 'mHwsZ9Bh5cK4Bz8utHjdhy'
        fun_ref = _convert_to_function_ref(CAPE_FUNCTION_ID)
        self.assertTrue(isinstance(fun_ref, pycape.function_ref.FunctionRef))

    def test_generate_nonce(self):
        length = 8
        nonce = _generate_nonce(length=length)
        self.assertTrue(isinstance(nonce, str))
        self.assertTrue(len(nonce), length)

    

if __name__ == '__main__':
    unittest.main()