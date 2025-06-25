import sys
import csv
import random

def generate_dummy_locations(num_points, bbox, output_file="dummy_locations.csv"):
    lat_max, lon_min, lat_min, lon_max = bbox
    
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["latitude", "longitude", "subjectid"])
        
        for _ in range(num_points):
            latitude = random.uniform(lat_min, lat_max)
            longitude = random.uniform(lon_min, lon_max)
            subject_id = random.randint(1000, 9999)
            writer.writerow([latitude, longitude, subject_id])
    
    print(f"Generated {num_points} locations in {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: generate_dummy_locations.py <num_points> '<lat_max, lon_min, lat_min, lon_max>'")
        print("Example (bounding box for germany): python .\generate_dummy_locations.py 1000 '55.0581, 5.8663, 47.2701, 15.0419'")
        sys.exit(1)
    
    num_points = int(sys.argv[1])
    bbox = list(map(float, sys.argv[2].strip('[]').split(',')))
    
    generate_dummy_locations(num_points, bbox)