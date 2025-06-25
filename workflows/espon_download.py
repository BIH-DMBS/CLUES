import os
import sys

# Append the target folder to sys.path
sys.path.append(os.path.join(os.getcwd(), 'utils'))
import espon

if __name__ == "__main__":
    json_file = sys.argv[1]
    vOI = sys.argv[2]
    dim = sys.argv[3]
    espon.get_asset_espon(json_file, vOI, dim)
