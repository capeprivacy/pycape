import pathlib

import pycape
from pycape.experimental import cli

CAPE_HOST = "wss://enclave.capeprivacy.com"
ECHO_DEPLOY_PATH = pathlib.Path(__file__).parent.absolute() / "echo"


cape = pycape.Cape(url=CAPE_HOST)
# Deploy Cape function
function_ref = cli.deploy(ECHO_DEPLOY_PATH)
message = cape.encrypt("Welcome to Cape".encode())
# Run Cape function
result = cape.run(function_ref, message)
print(f"The result is: {result.decode()}")
