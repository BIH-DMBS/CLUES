import os
import sys

# Append the target folder to sys.path
sys.path.append(os.path.join(os.getcwd(), 'utils'))
import modis

if __name__ == "__main__":
    json_file = sys.argv[1]
    name = sys.argv[2]
    year = sys.argv[3]
    print(json_file)
    print(name)
    print(year)
    modis.get_modis_vi(json_file, name, year)