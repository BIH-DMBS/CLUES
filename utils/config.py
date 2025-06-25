import os
import json

# Load the configuration file
config_path = os.path.join(os.getcwd(),'config', 'config.json')

with open(config_path, 'r') as config_file:
    config = json.load(config_file)

# Access the configuration settings
download_folder = config['download_folder']
years = config['years']
area = config['area']
configs_assets_folder = config['configs_assets_folder']
config_folder = config['config_folder']
secrets_folder = config['secrets_folder']
tmp_folder = config['tmp_folder']
espon_filename_length = config['espon_filename_length']

# Path to first configuration file
def getDownloadLocation():
    config_file = os.path.join(os.getcwd(), 'config', 'config.json')
    with open(config_file, 'r') as f:
        config = json.load(f)
    return config['download_folder']