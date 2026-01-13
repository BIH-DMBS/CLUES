import requests
import os
import yaml
import cdsapi
import earthaccess

# to download data access token from copernicus a needed
def get_copernicus_odata_token(sct_fldr):
    # The function retrieves an access token from the Copernicus Data Space Ecosystem (CDSE).
    # It extracts the access token from the response and returns it.
    url = 'https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token'
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # Create a client for the CDS API
    credential_file = os.path.join(sct_fldr, 'copernicus_credential.sct')

    with open(credential_file, 'r') as f:
            credentials = yaml.safe_load(f)

    response = requests.post(url, headers=headers, data=credentials)

    # Access the generated access token
    access_token = response.json().get('access_token')
    
    if access_token is not None:
        print("Copernicus DEM: token retrieved successfully.")
    else:   
        print("Copernicus DEM: Failed to retrieve access token.")

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