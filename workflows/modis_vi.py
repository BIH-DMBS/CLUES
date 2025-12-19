import os
import sys

# Append the target folder to sys.path
sys.path.append(os.path.join(os.getcwd(), 'utils'))
import modis

if __name__ == "__main__":
    json_file = sys.argv[1]
    vars_name = sys.argv[2]
    var = sys.argv[3]
    year = sys.argv[4]
    print(json_file)
    print(vars_name)
    print(var)
    print(year)
    modis.get_modis_vi(json_file, vars_name, var, year)

