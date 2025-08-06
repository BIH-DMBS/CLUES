import os
import sys

# TODO: Add exception handling for path operations - could raise OSError
# Append the target folder to sys.path
sys.path.append(os.path.join(os.getcwd(), 'utils'))
import utils

if __name__ == "__main__":
    # TODO: Add exception handling for command line arguments:
    # - IndexError: Insufficient command line arguments
    # - Add argument validation for file paths and parameter values
    json_file = sys.argv[1]
    vOI = sys.argv[2]
    year = sys.argv[3]
    # TODO: Add exception handling for utils.get_asset_atmosphere():
    # - All exceptions from CDS API calls, file operations, network errors
    # - Should catch and log errors instead of crashing the workflow
    utils.get_asset_atmosphere(json_file, year, vOI)