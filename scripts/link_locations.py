import netCDFutils
import geoTIFFutils
import multiprocessing
import os
import sys
from collections import defaultdict

def group_files_by_folder(file_list):
    folder_dict = defaultdict(list)
    
    for file in file_list:
        folder = os.path.dirname(file)
        folder_dict[folder].append(file)
    
    return list(folder_dict.values())

def worker_netcdf(input):
    subjects, netCDFList, pntcoord, resultfile = input
    print('-----Create-----')
    print(resultfile)
    print('-----link locations to-----')
    for netCDF_file in netCDFList:
        print(netCDF_file)
    print('-----processing-----')
    # Check if the result file already exists
    if os.path.exists(resultfile):
        print(f"Result file {resultfile} already exists. Skipping.")
        return
    dataOI = netCDFutils.netCDF_Link(subjects, netCDFList, pntcoord)
    print('Save the result to:' + resultfile)
    with open(resultfile, "w") as file:
        file.write(dataOI)

def worker_tiff(input):
    subjects, tiffList, pntcoord, resultfile = input
    print('-------------------------------------')
    print(resultfile)
    print('#####################################')
    # Check if the result file already exists
    if os.path.exists(resultfile):
        print(f"Result file {resultfile} already exists. Skipping.")
        return
    parameter = geoTIFFutils.getparam(tiffList)
    print(parameter)
    #geoTiffLinker(subjects, geoTIFF_Filelist, parameter):
    dataOI = geoTIFFutils.geoTiffLinker(subjects, tiffList, parameter)
    #print('Save the pretty JSON to:' + resultfile)
    # Save DataFrame to CSV
    dataOI.to_csv(resultfile, index=False)  # Set index=False to avoid saving the row numbers as a column

if __name__ == "__main__":
    # python .\link_locations.py .\dummy_locations.csv C:\code\DEGDB\degdb_utils\data C:\test 10

    print('get subjects')
    subjectfile = sys.argv[1]
    print(subjectfile)
    subjects = netCDFutils.getsubj(subjectfile)
    print(subjects)

    # get netcdf files to be linked  
    map_dir= sys.argv[2]

    print('-------- netCDFs --------')
    netCDFList = netCDFutils.getNetCDFList(map_dir)
    if len(netCDFList)>0:
        print(netCDFList)

        resultfolder=sys.argv[3]
        resultfile_template = resultfolder+'\\result'

        # number of jobs
        chunks = 50 #int(sys.argv[4])

        sublist_size = len(netCDFList) // chunks
        print('Use list comprehension to split the original list into sub-lists')
        #netCDFList = [netCDFList[i:i+sublist_size] for i in range(0, len(netCDFList), sublist_size)]
        netCDFList = group_files_by_folder(netCDFList)

        print("Create a Pool of worker processes")
        pool = multiprocessing.Pool(processes=16)  # You can specify the number of processes you want to run in parallel

        print('Create a list of input tuples')
        inpt = []
        for i in range(len(netCDFList)):
            inpt.append((subjects, netCDFList[i], 'geometry', resultfile_template + str(i) + '.json'))
        
        print('Link')
        print('Map the worker function to the input tuples in parallel')
        pool.map(worker_netcdf, inpt)

        print('Close the pool and wait for the worker processes to finish')
        pool.close()
        pool.join()

    print('-------- GeoTIFFs --------')

    # number of jobs
    chunks = 25

    print('get GeoTiffs')
    tiffList = geoTIFFutils.getTiffList(map_dir)
    if len(tiffList)>0:
        print(len(tiffList))

        print('Calculate the size of each sub-list')
        sublist_size = len(tiffList) // chunks
        print('Use list comprehension to split the original list into 10 sub-lists')
        tiffList = [tiffList[i:i+sublist_size] for i in range(0, len(tiffList), sublist_size)]
        print(tiffList)
        print('list of netCDFFilelists ready')

        
        print("Create a Pool of worker processes")
        pool = multiprocessing.Pool(processes=16)  # You can specify the number of processes you want to run in parallel

        print('Create a list of input tuples')
        inpt = []
        for i in range(0,chunks):
            inpt.append((subjects, tiffList[i], 'geometry', resultfile_template + str(i) + '.csv'))
        
        print('Link')
        print('Map the worker function to the input tuples in parallel')
        pool.map(worker_tiff, inpt)

        print('Close the pool and wait for the worker processes to finish')
        pool.close()
        pool.join()