import os
import sys

# Append the target folder to sys.path
sys.path.append(os.path.join(os.getcwd(), 'utils'))
import corine

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python workflows/corine_land_cover.py <config json> <variable>")
    json_file = sys.argv[1]
    vOI = sys.argv[2]
    corine.get_corine(json_file, vOI)
