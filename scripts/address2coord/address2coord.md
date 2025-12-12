# geocode_addresses.py

Script for converting addresses to geographic coordinates.

## Usage

```bash
python geocode_addresses.py <input_file> <output_file>
```

## Features

- Batch geocoding of addresses
- Multiple geocoding provider support
- Error handling and logging
- CSV input/output support

## Example

```python
from geocode_addresses import geocode_batch

results = geocode_batch('addresses.csv')
results.to_csv('coordinates.csv')
```