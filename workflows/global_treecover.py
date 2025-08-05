import os
import sys

# Append the target folder to sys.path
sys.path.append(os.path.join(os.getcwd(), 'utils'))
import global_tc


if __name__ == "__main__":
    json_file = sys.argv[1]
    name = sys.argv[2]
    global_tc.getTC_global(json_file, name)