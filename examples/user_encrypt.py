import pathlib

import pycape

parent_dir = pathlib.Path(__file__).parent.absolute()
function_json = parent_dir / "echo.json"
token_file = parent_dir / "user.token"

cape = pycape.Cape()
function_ref = cape.function(function_json)
token = cape.token(token_file)

print(f"Encrypting data with `pycape-dev` key for {function_ref.full_name} function...")
print()
# Two options to encrypt for a Cape user

# 1 - retrieve the user's key with cape.key, and pass the key to cape.encrypt
capedev_key = cape.key(username="pycape-dev")
encrypted_data = cape.encrypt(
    b"*** we encrypted against an explicit key ***", key=capedev_key
)
result = cape.run("pycape-dev/echo", token, encrypted_data)
print(result.decode())
print()

# 2 - pass username directly to cape.encrypt
encrypted_data = cape.encrypt(
    b"*** we encrypted for the 'pycape-dev' user ***", username="pycape-dev"
)
result = cape.run(function_ref, token, encrypted_data)
print(result.decode())
