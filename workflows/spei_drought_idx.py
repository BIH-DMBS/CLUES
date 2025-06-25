import os
import sys

# Append the target folder to sys.path
sys.path.append(os.path.join(os.getcwd(), 'utils'))
import utils

if __name__ == "__main__":
    print(sys.argv)
    json_file = sys.argv[1]
    year = sys.argv[2]
    utils.spei_download(json_file,year)