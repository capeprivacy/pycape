import re
import sys


img_tags = re.compile(r"(<img[^>]+)(?<!/)>", flags=re.M)
img_tag_styles = re.compile("style=\"float:right;\"", flags=re.M)

def main(file, newfile):
    with open(file, 'r') as fr:
        contents = fr.read()
        contents = img_tags.sub(r"\1 />", contents)
        contents = img_tag_styles.sub(r"style={{ float: 'right' }}", contents)
    with open(newfile, 'w') as fw:
        fw.write(contents)
    

if __name__ == "__main__":
    file = sys.argv[1]
    newfile = sys.argv[2]
    main(file, newfile)

