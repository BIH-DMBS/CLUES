import os
import sys

# Append the target folder to sys.path
sys.path.append(os.path.join(os.getcwd(), 'utils'))
import filter_neighborhood

if __name__ == "__main__":
    json_file = sys.argv[1]
    vOI = sys.argv[2]
    mode = sys.argv[3]
    print(json_file)
    print(vOI)
    print(mode)
    filter_neighborhood.compute_neighborhood(json_file, vOI, mode)