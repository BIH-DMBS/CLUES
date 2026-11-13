import os
import sys

# Append the target folder to sys.path
sys.path.append(os.path.join(os.getcwd(), 'utils'))
import treecover

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python workflows/treecover_download.py <config json> <variable>")
    json_file = sys.argv[1]
    vOI = sys.argv[2]
    treecover.get_treecover(json_file, vOI)
