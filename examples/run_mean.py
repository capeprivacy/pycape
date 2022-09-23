import os
import pathlib

from pycape import Cape
from pycape import FunctionRef

if __name__ == "__main__":
    url = os.environ.get("CAPE_HOST", "wss://enclave.capeprivacy.com")
    token_file = os.environ.get("TOKEN_FILE", "mean_token.json")
    token_file = pathlib.Path(__file__).parent.absolute() / token_file

    function_ref = FunctionRef.from_json(token_file)

    cape = Cape(url=url)

    x = [1, 2, 3, 4]
    result = cape.run(function_ref, x, use_serdio=True)

    print(f"The mean of x is: {result}")
