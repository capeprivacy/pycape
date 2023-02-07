import pathlib

import pycape
from pycape.experimental import cli

CAPE_HOST = "https://app.capeprivacy.com"
ECHO_DEPLOY_PATH = pathlib.Path(__file__).parent.absolute() / "echo"


cape = pycape.Cape(url=CAPE_HOST)
# Deploy Cape function with current CLI user
function_ref = cli.deploy(ECHO_DEPLOY_PATH)
print("Echo deployed:")
print(f"\t- ID: {function_ref.id}")
print(f"\t- Checksum: {function_ref.checksum}")
print()

# Create short-lived personal access token for current CLI user
token = cli.token()
print("Token generated:")
print(f"\t- Token: {token.raw}")
print()

# Encrypt input for current CLI user
print("Encrypting input for current CLI user...")
print()
message = cape.encrypt("Welcome to Cape".encode())

# Run Cape function, using PAT from above
print("Running echo function...")
print()
result = cape.run(function_ref, token, message)
print(f"The result is: {result.decode()}")
