import os
import sys

# Append the target folder to sys.path
sys.path.append(os.path.join(os.getcwd(), 'utils'))
import worldPopDownload

if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit("Usage: python workflows/worldpop.py <config json> <variable> <year>")
    json_file = sys.argv[1]
    vOI = sys.argv[2]
    year = sys.argv[3]
    worldPopDownload.getWorldPop(json_file, year, vOI)