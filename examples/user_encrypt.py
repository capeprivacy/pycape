import pathlib

import pycape

function_json = pathlib.Path(__file__).parent.absolute() / "echo_token.json"
function_ref = pycape.FunctionRef.from_json(function_json)

cape = pycape.Cape()

# Two options to encrypt for a Cape user

# 1 - retrieve the user's key with cape.key, and pass the key to cape.encrypt
capedocs_key = cape.key(username="capedocs")
encrypted_data = cape.encrypt(b"encrypt against capedocs's key", key=capedocs_key)
result = cape.run(function_ref, encrypted_data)
print(result.decode())

# 2 - pass username directly to cape.encrypt
encrypted_data = cape.encrypt(
    b"quickly encrypt my data for capedocs", username="capedocs"
)
result = cape.run(function_ref, encrypted_data)
print(result.decode())
