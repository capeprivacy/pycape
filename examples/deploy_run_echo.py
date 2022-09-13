import subprocess

from pycape import Cape
from pycape import FunctionRef

CAPE_HOST = "wss://enclave.capeprivacy.com"

# Cape deploy function
proc_deploy = subprocess.Popen(
    "cape deploy ./echo --url " + CAPE_HOST,
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
out_deploy, err_deploy = proc_deploy.communicate()
err_deploy = err_deploy.decode()

# Parse stderr to get CAPE_FUNCTION_ID and CAPE_FUNCTION_CHECKSUM
err_deploy = err_deploy.split("\n")
for i in err_deploy:
    if "Function ID" in i:
        function_id = i.split(" ")
        CAPE_FUNCTION_ID = function_id[3]
    elif "Checksum" in i:
        checksum = i.split(" ")
        CAPE_FUNCTION_CHECKSUM = checksum[2]

# Run function
function_ref = FunctionRef(CAPE_FUNCTION_ID, CAPE_FUNCTION_CHECKSUM)
cape = Cape(url=CAPE_HOST)
input = "Welcome to Cape".encode()
result = cape.run(function_ref, input)
print(f"The result is: {result.decode()}")
