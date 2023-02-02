import pathlib

import pycape
from pycape.experimental import cli

CAPE_HOST = "https://app.capeprivacy.com"
ECHO_DEPLOY_PATH = pathlib.Path(__file__).parent.absolute() / "echo"


cape = pycape.Cape(url=CAPE_HOST)
# Deploy Cape function
function_ref = cli.deploy(ECHO_DEPLOY_PATH, token_expiry=100)
print("Echo deployed:")
print(f"\t- ID: {function_ref.id}")
print(f"\t- Token: {function_ref.token}")
print(f"\t- Checksum: {function_ref.checksum}")
# Encrypt input
message = cape.encrypt("Welcome to Cape".encode(), token=function_ref.token)
# Run Cape function
result = cape.run(function_ref, message)
print(f"The result is: {result.decode()}")
