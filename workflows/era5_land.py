import os
import sys

# Append the target folder to sys.path
sys.path.append(os.path.join(os.getcwd(), 'utils'))
import era5Land

if __name__ == "__main__":
    json_file = sys.argv[1]
    vOI = sys.argv[2]
    year = sys.argv[3]
    era5Land.getEra5Land(json_file, year, vOI)