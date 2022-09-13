import pathlib
import subprocess

import pycape

CAPE_HOST = "wss://enclave.capeprivacy.com"
ECHO_DEPLOY_PATH = pathlib.Path(__file__).parent.absolute() / "echo"

# Cape deploy function
proc_deploy = subprocess.Popen(
    f"cape deploy {ECHO_DEPLOY_PATH} --url {CAPE_HOST}",
    shell=True,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
out_deploy, err_deploy = proc_deploy.communicate()
err_deploy = err_deploy.decode()

# Parse stderr to get function id & function checksum
err_deploy = err_deploy.split("\n")
function_id = function_checksum = None
for i in err_deploy:
    if "Function ID" in i:
        id_output = i.split(" ")
        function_id = id_output[3]
    elif "Checksum" in i:
        checksum_output = i.split(" ")
        function_checksum = checksum_output[2]

if function_id is None:
    raise RuntimeError(f"Function ID not found in 'deploy' response: \n{err_deploy}")

# Run function
function_ref = pycape.FunctionRef(function_id, function_checksum)
cape = pycape.Cape(url=CAPE_HOST)
message = cape.encrypt("Welcome to Cape".encode())
result = cape.run(function_ref, message)
print(f"The result is: {result.decode()}")
