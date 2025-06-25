# Enrichment of geolaoction data

The framework includes scripts to enrich location data. 

## Simple point data

The simplest situation is to have a csv files that contains the loaction and some ID.
<pre>
latitude,longitude,subjectid
51.876259173091015,14.24452287575035,7858
52.09913944097461,13.654840491247233,3406
53.424305699033326,13.453464611332228,8017
</pre>

The script */scripts/link_loactions.py* processes netCDF and GeoTIFF files located in the input folder, linking the locations specified in the location.csv file to the corresponding features. 

<pre>python link_locations.py locations.csv input_folder output_folder</pre>

The location.csv file should contain at least three columns: longitude, latitude, and subject ID. The results of this enrichment process are saved in the output folder, with JSON files for features available as netCDF and CSV files for GeoTIFF features.

## Link areas

tdDo
