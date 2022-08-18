import subprocess

from pycape import Cape
from pycape import FunctionRef
from pycape.cape import _convert_to_function_ref, _generate_nonce
import pycape

CAPE_HOST = "wss://enclave.capeprivacy.com"

# Cape deploy function
proc_deploy = subprocess.Popen(
    "cape deploy ../../examples/echo --url " + CAPE_HOST,
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

# Run function
# function_ref = FunctionRef(CAPE_FUNCTION_ID, CAPE_FUNCTION_HASH)
# print(CAPE_FUNCTION_ID)
# fun_ref = _convert_to_function_ref(CAPE_FUNCTION_ID)
# print(isinstance(fun_ref, pycape.function_ref.FunctionRef))

function_ref = FunctionRef(CAPE_FUNCTION_ID, CAPE_FUNCTION_HASH)

cape = Cape(url=CAPE_HOST)
print(cape._loop)
cape.connect(function_ref)
print(cape._loop)
cape.close()
print(cape._loop)

print(len(_generate_nonce()))

# input = "Welcome to Cape".encode()
# cape.run(function_ref, input)
# print(cape._loop)
# print(cape.connect(function_ref))
# print(cape._loop)
# result = cape.invoke(b"Hello Alice!")
# print(result.decode())

# print("close now")
# input = "Welcome to Cape".encode()
# result = cape.run(function_ref, input)
# print(f"The result is: {result.decode()}")

# print(cape.close())


