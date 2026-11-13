import os
import yaml
import cdsapi
import earthaccess

def check_credential_atmosphere(sct_fldr):
    try:
        # Create a client for the CDS API
        file = os.path.join(sct_fldr, 'cdsapirc_atmo.sct')
        with open(file, 'r') as f:
                credentials = yaml.safe_load(f)
    except Exception as e:
        print(f"An error occurred: {e}")

    try:
        # get the client
        c = cdsapi.Client(url=credentials['url'], key = '')#key=credentials['key'])
        print("Copernicus atmosphere credentials: CDS API client created successfully.")
    except Exception as e:
        print(f"Copernicus atmosphere credentials: An error occurred: {e}")


def check_credential_climate(sct_fldr):
    try:
        # Create a client for the CDS API
        file = os.path.join(sct_fldr, 'cdsapirc_climate.sct')
        with open(file, 'r') as f:
                credentials = yaml.safe_load(f)
    except Exception as e:
        print(f"An error occurred: {e}")

    try:
        # get the client
        c = cdsapi.Client(url=credentials['url'], key = '')#key=credentials['key'])
        print("Copernicus atmosphere climate credentials: CDS API client accessible.")
    except Exception as e:
        print(f"Copernicus atmosphere climate credentials: An error occurred: {e}")


def check_earthdata_credential():
    try:
        earthaccess.login(strategy="netrc")
        print("Earthdata Login: Credentials are valid.")
    except Exception as e:
        print(f"Earthdata Login: An error occurred: {e}")