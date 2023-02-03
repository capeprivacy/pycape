import os
import pathlib

from pycape import Cape

function_json = pathlib.Path(__file__).parent.absolute() / "mean.json"
token_file = pathlib.Path(__file__).parent.absolute() / "capedocs.token"

function_id_env = os.environ.get("FUNCTION_ID")
token_env = os.environ.get("TOKEN")

cape = Cape()
function_ref = cape.function(function_json)
token = cape.token(token_file)

if __name__ == "__main__":
    x = [1, 2, 3, 4]
    print(f"Running function '{function_ref.full_name}' on {x}...")

    result = cape.run(function_ref, token, x, use_serdio=True)

    print(f"The mean of {x} is: {result}")
