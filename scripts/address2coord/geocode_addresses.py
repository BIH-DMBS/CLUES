import pandas as pd
from geopy.geocoders import Nominatim
from time import sleep

'''
This script reads a semicolon-separated CSV containing addresses and uses
Nominatim (OpenStreetMap) to geocode each one into WGS84 latitude/longitude.
The output is saved to a new CSV with added Latitude and Longitude columns.

How to use:
1. Put your input file in the same folder and name it "addresses.csv"
   (semicolon-separated: ID;ZipCode;Country;Town;Adresse)
2. Run the script:  python geocode_csv.py
3. A new file "addresses_with_coords.csv" will be created with coordinates.
4. Note: PO Box addresses may not return results; Nominatim requires a
   1-second delay between requests to avoid rate limiting. (For heavy workloads, consider a paid geocoder (Google, Here, Mapbox).)
'''

# Input and output files
INPUT_CSV = "addresses.csv"
OUTPUT_CSV = "addresses_with_coords.csv"

# Create geocoder
geolocator = Nominatim(user_agent="geo_script")

# Read semicolon-separated CSV
df = pd.read_csv(INPUT_CSV, sep=';')

# Prepare new columns
df["Latitude"] = None
df["Longitude"] = None

for idx, row in df.iterrows():
    address_str = f"{row['Adresse']}, {row['Town']}, {row['ZipCode']}, {row['Country']}"
    print(f"Geocoding: {address_str}")

    try:
        loc = geolocator.geocode(address_str)
        if loc:
            df.at[idx, "Latitude"]  = loc.latitude
            df.at[idx, "Longitude"] = loc.longitude
            print(f" → OK: {loc.latitude}, {loc.longitude}")
        else:
            print(" → Not found")
    except Exception as e:
        print("Error:", e)

    sleep(1)  # polite delay to avoid rate limiting

# Save result
df.to_csv(OUTPUT_CSV, sep=';', index=False)
print(f"\nSaved: {OUTPUT_CSV}")