import os
import sys

sys.path.append(os.path.join(os.getcwd(), 'utils'))

import copernicusDEM

if __name__ == "__main__":
    #print(sys.argv)
    json_file = sys.argv[1]
    vOI = sys.argv[2] 
    print(vOI)
    copernicusDEM.getInfoCopenicusDEM(json_file,vOI)
    
