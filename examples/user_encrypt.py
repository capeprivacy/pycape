import pathlib

import pycape

parent_dir = pathlib.Path(__file__).parent.absolute()
function_json = parent_dir / "echo.json"
token_file = parent_dir / "capedocs.token"

cape = pycape.Cape()
fref = cape.function(function_json)
token = cape.token(token_file)

print(f"Encrypting data with `capedocs` key for {fref.full_name} function...")
print()
# Two options to encrypt for a Cape user

# 1 - retrieve the user's key with cape.key, and pass the key to cape.encrypt
capedocs_key = cape.key(username="capedocs")
encrypted_data = cape.encrypt(
    b"*** we encrypted against an explicit key ***", key=capedocs_key
)
result = cape.run("capedocs/echo", token, encrypted_data)
print(result.decode())
print()

# 2 - pass username directly to cape.encrypt
encrypted_data = cape.encrypt(
    b"*** we encrypted for the 'capedocs' user ***", username="capedocs"
)
result = cape.run(fref, token, encrypted_data)
print(result.decode())
