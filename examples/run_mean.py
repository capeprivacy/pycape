import os

from pycape import Cape
from pycape import FunctionRef

if __name__ == "__main__":
    token = os.environ.get("CAPE_TOKEN", None)
    url = os.environ.get("CAPE_HOST", "wss://enclave.capeprivacy.com")
    function_id = os.environ.get(
        "CAPE_FUNCTION_ID", "e4c2a674-9c7f-42d3-8ade-63791c16c3c7"
    )
    function_hash = os.environ.get("CAPE_FUNCTION_HASH", None)

    if function_hash is None:
        function_ref = function_id
    else:
        function_ref = FunctionRef(function_id, function_hash)

    cape = Cape(url=url, access_token=token)

    x = [1, 2, 3, 4]
    result = cape.run(function_ref, x, use_serdio=True)

    print(f"The mean of x is: {result}")
