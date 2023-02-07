import os
import pathlib

from pycape import Cape

function_json = pathlib.Path(__file__).parent.absolute() / "mean.json"
token_file = pathlib.Path(__file__).parent.absolute() / "user.token"

function_id_env = os.environ.get("FUNCTION_ID")
token_env = os.environ.get("TOKEN")

f = function_id_env or function_json
t = token_env or token_file

cape = Cape()
function_ref = cape.function(f)
token = cape.token(t)

if __name__ == "__main__":
    x = [1, 2, 3, 4]
    print(f"Running function '{function_ref.full_name}' on {x}...")

    result = cape.run(function_ref, token, x, use_serdio=True)

    print(f"The mean of {x} is: {result}")
