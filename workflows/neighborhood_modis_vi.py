import os
import sys

# Append the target folder to sys.path
sys.path.append(os.path.join(os.getcwd(), 'utils'))
import filter_neighborhood

if __name__ == "__main__":
    json_file = sys.argv[1]
    typ = sys.argv[2]
    name = sys.argv[3]
    fltr = sys.argv[4]
    rds = sys.argv[5]
    year = sys.argv[6]
    print(json_file)
    print(typ)
    print(name)
    print(fltr)
    print(rds)
    print(year) 
    filter_neighborhood.compute_neighborhood_modis_vi(json_file, typ, name, fltr, rds, year)