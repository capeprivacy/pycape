import pathlib

import pycape

CAPE_HOST = "wss://enclave.capeprivacy.com"
ECHO_DEPLOY_PATH = pathlib.Path(__file__).parent.absolute() / "echo"


cape = pycape.Cape(url=CAPE_HOST)
# Deploy Cape function
function_ref = cape.deploy(ECHO_DEPLOY_PATH)
# function_ref = pycape.FunctionRef(id="jXScaKkrksFbVAWQidDAXY", token="eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqWFNjYUtrcmtzRmJWQVdRaWREQVhZIiwiZXhwIjoxNjYzMjg3ODY4LCJpYXQiOjE2NjMyODQyNjh9.s7ZvMrSqPg_Oci3K4WngDbKYQ5slmRORxmd5S1aqwub0YWJcn-5aMoZbjS05uaXhvfLdaXDgzQ-SvJJRj5jhNpAYjXEBIXi-zPGDyqJJTA_ipy_4zMOqEEYDd4sKsszsDKatsNxg0Maxomzfhmxac-eI7o7Q4JPIiJHuAsn7e1iqYq3WbYW17E85lP9VIA8p3zQDlzBbeg0gwCuy8IctMlF0zj62WZ8exSnejdULY0v3YIQE2WfFnj38GHZTQYJqLfsgEYTlPDEkYkdlcUe5a6CXmdxwVLU7XFrHcui8jwqwH8P1Uc9A-WZoiIVNh1mLIcsuUugvWSuX0U914aL6Hg")
message = cape.encrypt("Welcome to Cape".encode())
# Run Cape function
result = cape.run(function_ref, message)
print(f"The result is: {result.decode()}")
