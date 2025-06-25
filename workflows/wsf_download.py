import os
import sys

# Append the target folder to sys.path
sys.path.append(os.path.join(os.getcwd(), 'utils'))
import wsf

if __name__ == "__main__":
    json_file = sys.argv[1]
    vOI = sys.argv[2]
    wsf.download_wsf(json_file, vOI)