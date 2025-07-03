# Third party accounts

To enable the CLUES framework to access certain geospatial datasets, users must register with specific data providers and generate personal access tokens.

## Copernicus (ECMWF)
Data from the Copernicus Climate Data Store (CDS) and the Atmosphere Data Store (ADS) requires a free account with the European Centre for Medium-Range Weather Forecasts (ECMWF).

### Step-by-Step

1. Create an ECMWF account at [ecmwf.int](https://www.ecmwf.int/)
2. Visit:
  - CDS API instructions at https://cds.climate.copernicus.eu/how-to-api
  - ADS API instructions at https://ads.atmosphere.copernicus.eu/how-to-api
3. Generate personalized API tokens from both platforms.

### Token Storage

Save the tokens in two separate files:

*cdsapirc_atmo.sct*
<pre>url: https://ads.atmosphere.copernicus.eu/api
key: place your token here</pre>

*cdsapirc_climate.sct*
<pre>url: https://cds.climate.copernicus.eu/api
key: place your token here</pre>

## NASA EarthData

Accessing vegetation indices (e.g., NDVI, EVI) from NASA’s Earthdata platform also requires registration.

### Step-by-Step

1. Register at [earthdata.nasa.gov](https://www.earthdata.nasa.gov/) 
2. Create a personal access token

### Token Storage
Create the following file:

*nasa.sct*
<pre>token: place your token here</pre>

## Notes
The location of the credential (.sct) files is defined in the general workflow configuration file **config.json** under the key: *configs_assets_folder*.
#### [For more details, see the Configuration Files guide.](setup.md)
