import hpke_spec


class TestHpkeSpec:
    def test_hpke_seal(self):
        pk = b"my fake public key is 32 bytes !"
        ptxt = b"hello, my name is Vincent Law"
        ciphertext = hpke_spec.hpke_seal(pk, ptxt)
        assert len(ciphertext) == 45

    def test_wrong_pk_size(self):
        
        try:
            pk = b"my fake public key is greater than 32 bytes !"
            ptxt = b"hello, my name is Vincent Law"
            _ = hpke_spec.hpke_seal(pk, ptxt)
        except:
            # the exception type is pyo3_runtime.PanicException,
            # which isn't accessible from Python.
            return
        raise AssertionError(
            "hpke_seal failed to raise Exception on malformed public key"
        )
        


        
