from pycape import Cape

if __name__ == "__main__":
    cape = Cape()
    input = 20
    result = cape.run("c052214b-a597-42fc-9a2f-d48ea9dc9902", input)
    print(f"The result is: {result}")