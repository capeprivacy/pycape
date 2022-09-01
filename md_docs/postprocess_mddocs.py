import re
import sys


reg = re.compile(r"(<img[^>]+)(?<!/)>", flags=re.M)

def main(file, newfile):
    with open(file, 'r') as fr:
        contents = fr.read()
        contents = reg.sub(r"\1 />", contents)
    with open(newfile, 'w') as fw:
        fw.write(contents)
    

if __name__ == "__main__":
    file = sys.argv[1]
    newfile = sys.argv[2]
    main(file, newfile)

