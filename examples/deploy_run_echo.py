import json
import os
import subprocess

from pycape import Cape
from pycape import FunctionRef

CAPE_HOST = "wss://hackathon.capeprivacy.com"

# Cape deploy function
proc_deploy = subprocess.Popen(
    "cape deploy ./echo --url " + CAPE_HOST,
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
out_deploy, err_deploy = proc_deploy.communicate()
err_deploy = err_deploy.decode()

# Parse stderr to get CAPE_FUNCTION_ID and CAPE_FUNCTION_HASH
err_deploy = err_deploy.split("\n")
for i in err_deploy:
    if "Function ID" in i:
        function_id = i.split(" ")
        CAPE_FUNCTION_ID = function_id[3]
    elif "Function Hash" in i:
        function_hash = i.split(" ")
        CAPE_FUNCTION_HASH = function_hash[3]

# Parse cape/auth for CAPE_TOKEN
HOME = os.getenv("HOME")
auth_file = f"{HOME}/.config/cape/auth"
f = open(auth_file)
cape_auth = json.load(f)
CAPE_TOKEN = cape_auth["access_token"]

# Run function
function_ref = FunctionRef(CAPE_FUNCTION_ID, CAPE_FUNCTION_HASH)
cape = Cape(url=CAPE_HOST, access_token=CAPE_TOKEN)
input = "Welcome to Cape".encode()
result = cape.run(function_ref, input)
print(f"The result is: {result.decode()}")
