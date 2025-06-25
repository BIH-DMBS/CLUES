## Third party accounts


To enable the framework to work some of the primary data sources require the user to have an account to get data access. 

For data associated to Copernicus a European Centre for Medium-Range Weather Forecasts (ECMWF) account is necessary to create a personal access token for access to atmosphere data store and climate data. 

Go to https://www.ecmwf.int/ and create account. For both services a CDS API personized access token must be generated. To do so visit Climate Data Store: https://cds.climate.copernicus.eu/how-to-api and Atmosphere Data Store: https://ads.atmosphere.copernicus.eu/how-to-api. 

The tokens need to be saved in the following files: *cdsapirc_climate.sct, cdsapirc_atmo.sct*.

The content of the files hast to look like this:

*cdsapirc_atmo.sct*
<pre>url: https://ads.atmosphere.copernicus.eu/api

key: place your token here</pre>

*cdsapirc_climate.sct*
<pre>url: https://cds.climate.copernicus.eu/api

key: place your token here</pre>

To access data associated with NASA earthdata (https://www.earthdata.nasa.gov/) credentials are required. Go to the webpage and create your account and the token you need. The *nasa.sct* file looks a little differnt:

*nasa.sct*
<pre>token: place your token here</pre>


The location of the credential *.sct files is defined in the config.json under the key: *configs_assets_folder*.