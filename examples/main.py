from pycape.cape import Cape

if __name__ == "__main__":
    cape = Cape(auth_token = "<YOUR_AUTH_TOKEN>")

    input = 20
    result = cape.run("c052214b-a597-42fc-9a2f-d48ea9dc9902", input)
    print(f"The result is: {result}")
