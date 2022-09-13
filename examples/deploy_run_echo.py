import os

from pycape import Cape

if __name__ == "__main__":
    token = os.environ.get("CAPE_TOKEN", None)
    url = os.environ.get("CAPE_HOST", "wss://enclave.capeprivacy.com")

    cape = Cape(url=url, access_token=token)
    function_ref = cape.deploy("echo/")
    input = "Welcome to Cape".encode()
    result = cape.run(function_ref, input)

    print(f"The result is: {result.decode()}")
