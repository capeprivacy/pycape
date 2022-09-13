import os

from pycape import Cape
from pycape import FunctionRef

if __name__ == "__main__":
    token = os.environ.get("CAPE_TOKEN", None)
    url = os.environ.get("CAPE_HOST", "wss://enclave.capeprivacy.com")
    function_id = os.environ.get("CAPE_FUNCTION_ID", "VNgMtygWv8wCwwjbbQ2kH6")
    checksum = os.environ.get("CAPE_CHECKSUM", None)

    if checksum is None:
        function_ref = function_id
    else:
        function_ref = FunctionRef(function_id, checksum)

    cape = Cape(url=url, access_token=token)
    input = "Welcome to Cape".encode()
    result = cape.run(function_ref, input)

    print(f"The result is: {result.decode()}")
