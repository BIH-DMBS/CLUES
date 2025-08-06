import os
import sys

# TODO: Add exception handling for path operations - could raise OSError
# Append the target folder to sys.path
sys.path.append(os.path.join(os.getcwd(), 'utils'))
import espon

if __name__ == "__main__":
    # TODO: Add exception handling for command line arguments:
    # - IndexError: Insufficient command line arguments
    # - Add argument validation for file paths and parameter values
    json_file = sys.argv[1]
    vOI = sys.argv[2]
    dim = sys.argv[3]
    # TODO: Add exception handling for espon.get_asset_espon():
    # - HTTP request errors, file download failures, ZIP extraction errors
    # - Should catch and log errors instead of crashing the workflow
    espon.get_asset_espon(json_file, vOI, dim)
