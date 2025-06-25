# Workflow config file

CLUES framework is customized by altering the *workflows\config\config.json*.

Most key-value pairs in the file should be self-explanatory:

example: *config.json*
<pre>
{
    "download_folder":"/clues/data",
    "tmp_folder":"/clues/tmp",
    "configs_assets_folder":"/clues/configs_sources_test",
    "config_folder":"/clues/config",
    "secrets_folder":"/clues/secrets",
    "years": ["2015", "2016", "2017", "2018", "2019", "2020", "2021", "2022","2023","2024","2025],
    "update_years":[2025],
    "area":"Europe",
    "espon_filename_length":80
}
</pre>

The key "espon_filename_length" is not that self-explanatory, the integer values set here is used to limit the filename lengths used while downloading the espon data. The filemname is generated from the naming and dimension of the differnt assets (https://database.espon.eu/api/). As single file cannot exceed 255 characters the limit is necessary. 

# Bounding boxes

CLUES framework comes with a predefined set of boundingboxes found in *workflows\config\bbox.json*. Custom bbox must also placed in this file. For example, the bounding box for Europe is represented as "Europe": [72, -15, 30, 42.5]. Here, 72 is the minimum longitude, -15 is the minimum latitude, 30 is the maximum longitude, and 42.5 is the maximum latitude. 

example: *bbox.json*
<pre>
{
    "Europe":[72, -15, 30, 42.5],
    "Germany":[55.0581, 5.8663, 47.2701, 15.0419],
    "UK":[60.8608, -8.6493, 49.9096, 1.7689],
    "Brandenburg":[53.5587, 11.2682, 51.3618, 14.7636],
    "Berlin":[52.7136,12.9673,52.2839,13.816],
    "Norway":[71.1850, 4.9921, 57.9586, 31.0781],
}
</pre>

# Source configuration files

Each of the primary data sources used by CLUES is utilized and custmized on the basis of a distinct config files. The base as curated by CLUES is located in the folder *workflows\config_sources*. The location of the used *configs_assets_folder* can be customized in the *config.json*. This files contain metadata on the primary sources. Each of the source config files loacted in the the folder *workflows\config_sources* contains a key *variables* that is linked to a list of the assets to download. To change what assets to download from the different sources removing items from the list is the way.

*cams-global-reanalysis-eac4.json*
<pre>
{
    "type":"atmosphere",
    "source":"cams-global-reanalysis-eac4",
    "file":"cams-global-reanalysis-eac4.json",
    "link": "https://ads.atmosphere.copernicus.eu/cdsapp#!/dataset/cams-global-reanalysis-eac4?tab=form",
    "citation":"Inness et al. (2019), http://www.atmos-chem-phys.net/19/3515/2019/",
    "start_year": "2003",
    "end_year": "2025",
    "delta_t_in_h":"3",
    "format": "netcdf",
    "variables":[
        {
            "name":"black_carbon_aerosol_optical_depth_550nm"
        },
        {
            "name":"dust_aerosol_optical_depth_550nm"
        },
        {
            "name":"organic_matter_aerosol_optical_depth_550nm"
        },
        {
            "name":"sea_salt_aerosol_optical_depth_550nm"
        },
        ...
    ]
}
</pre>