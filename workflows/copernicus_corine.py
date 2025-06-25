import os
import sys

# Append the target folder to sys.path
sys.path.append(os.path.join(os.getcwd(), 'utils'))
import utils

if __name__ == "__main__":
    json_file = sys.argv[1]
    vOI = sys.argv[2]
    utils.copenicus_corine(json_file, vOI)