import os

from pycape import Cape
from pycape import FunctionRef

if __name__ == "__main__":
    token = os.environ.get("CAPE_TOKEN", None)
    url = os.environ.get("CAPE_HOST", "wss://enclave.capeprivacy.com")
    function_id = os.environ.get("CAPE_FUNCTION_ID", "VNgMtygWv8wCwwjbbQ2kH6")
    function_hash = os.environ.get("CAPE_FUNCTION_HASH", None)

    if function_hash is None:
        function_ref = function_id
    else:
        function_ref = FunctionRef(function_id, function_hash)

    cape = Cape(url=url, access_token=token)
    cape.connect(function_ref)

    result = cape.invoke("Hello Cape".encode())
    print(f"The result is: {result.decode()}")

    result = cape.invoke("Hello Gavin".encode())
    print(f"The result is: {result.decode()}")

    result = cape.invoke("Hello Hello".encode())
    print(f"The result is: {result.decode()}")

    cape.close()
