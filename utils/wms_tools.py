from owslib.wms import WebMapService
import json

def get_eoc_atmosphere_config_json():
    url = "https://geoservice.dlr.de/eoc/atmosphere/wms"
    wms = WebMapService(url, version='1.3.0')
    # Iterate over the layers and print their metadata
    items = []
    for layer_name, layer in wms.contents.items():
        item = {}
        item['name'] = layer_name
        item['abstract'] = layer.abstract
        item['temporal_dimension'] = layer.dimensions['time']['values'][0]
        item['width'] = 1000
        item['height'] = 1000
        items.append(item)

    print(items)

    eoc_atmosphere = {
        "type": "wms",
        "source": "EOC-Atmosphere-Coverage-Service",
        "file":"EOC_Atmosphere_Coverage_Service.json",
        "link": "https://geoservice.dlr.de/eoc/atmosphere/wms",
        "format": "image/geotiff",
        "crs":"EPSG:4326",
        "variables":items,
    }

    # Write to a text file
    with open('EOC_Atmosphere_Coverage_Service.json', 'w') as file:
        json.dump(eoc_atmosphere, file, indent=4)


def get_eoc_elevation_map_service_config_json():
    not_of_interest = [
        "srtm_x-sar_hem_mosaic",
        "TDM_POLARDEM_ANT_COASTLINE",
        "TDM_POLARDEM90_ANT_HSM",
        "TDM_POLARDEM90_ANT_HSC",
        "TDM_POLARDEM90_ANT_DEM",
        "TDM90_HEM",
        "TDM90_COV",
        "TDM90_COM",
        "srtm_x-sar_mosaic",
        "srtm_x-sar_hillshade_mosaic",
        "srtm_x-sar_dem_mosaic",
        "TDM90_AM2",
        "TDM90_AMP",
        "TDM90_LSM",
    ]
    # Iterate over the layers and print their metadata
    items = []
    for layer_name, layer in wms.contents.items():
        if layer_name not in not_of_interest:
            item = {}
            item['name'] = layer_name
            item['abstract'] = layer.abstract
            item['width'] = 1000
            item['height'] = 1000
            items.append(item)

    eoc_elevation = {
        "type": "wms",
        "source": "EOC_Elevation_Map_Service",
        "file":"EOC_Elevation_Map_Service.json",
        "link": "https://geoservice.dlr.de/eoc/elevation/wms",
        "format": "image/geotiff",
        "crs":"EPSG:4326",
        "variables":items,
    }

    # Write to a text file
    with open('EOC_Elevation_Map_Service.json', 'w') as file:
        json.dump(eoc_elevation, file, indent=4)


def get_eoc_land_map_service_config_json():
    not_of_interest = [
        "CORINE_LAND_COVER_1990_1000x1000_ETRS89",
        "CORINE_LAND_COVER_1990_1000x1000_LAEA",
        "CORINE_LAND_COVER_1990_250x250_ETRS89",
        "CORINE_LAND_COVER_1990_250x250_LAEA",
        "CORINE_LAND_COVER_2000_1000x1000_ETRS89",
        "CORINE_LAND_COVER_2000_1000x1000_LAEA",
        "CORINE_LAND_COVER_2000_250x250_ETRS89",
        "CORINE_LAND_COVER_2000_250x250_LAEA",
        "CORINE_LAND_COVER_2006_1000x1000_ETRS89",
        "CORINE_LAND_COVER_2006_1000x1000_LAEA",
        "CORINE_LAND_COVER_2006_250x250_ETRS89",
        "CORINE_LAND_COVER_2006_250x250_LAEA",
        "FOREST_AREAS_DISTRICTS_PRY_P1Y",
        "FOREST_COVER_PRY_1986_2020_P1Y",
        "FOREST_COVER_S2_PRY",
        "FOREST_FHD_S2_PRY",
        "FOREST_FRAGMENTATION_PRY_2000",
        "FOREST_FRAGMENTATION_PRY_2010",
        "FOREST_FRAGMENTATION_PRY_2020",
        "FOREST_PAI_S2_PRY",
        "FOREST_RH95_S2_PRY",
        "FOREST_STRUCTURE_DE_AGBD_P1Y",
        "FOREST_STRUCTURE_DE_COVER_P1Y",
        "FOREST_STRUCTURE_DE_RH95_P1Y",
        "GSP_DAILY",
        "GSP_SCD",
        "GSP_SCDE_MEAN",
        "GSP_SCDE_P1Y",
        "GSP_SCDL_MEAN",
        "GSP_SCDL_P1Y",
        "GSP_SCD_MEAN",
        "GSP_SCD_P1Y",
        "GSP_SCENRT_P1D",
        "GSP_SCE_P1D",
        "GUF04_DLR_v1_Mosaic",
        "GUF28_DLR_v1_Mosaic",
        "GWP_P1M",
        "GWP_P1Y",
        "GWP_REL_P1M",
        "GWP_REL_P1Y",
        "ICELINES_S1_P1M",
        "ICELINES_S1_P1Y",
        "ICELINES_SHELFNAMES",
        "IDC_Score"
        "LCC_DE_2015",
        "NOAA_AVHRR_SST_P1M",
        "PROTECTED_AREAS_FOREST_PRY",
        "IDC_Score",
        "LCC_DE_2015",
        "TDM_FNF50_COV",
        "TDM_FNF50_SPC",
        "TDM_FNF50_SPD",
        "TREE_CANOPY_COVER_LOSS_HA_ALLFOREST_P1Y",
        "TREE_CANOPY_COVER_LOSS_HA_CONIFEROUS_P1Y",
        "TREE_CANOPY_COVER_LOSS_HA_DECIDUOUS_P1Y",
        "TREE_CANOPY_COVER_LOSS_PERC_ALLFOREST_P1Y",
        "TREE_CANOPY_COVER_LOSS_PERC_CONIFEROUS_P1Y",
        "TREE_CANOPY_COVER_LOSS_PERC_DECIDUOUS_P1Y",
        "URMO_TAM_3K_BRUNSWICK",
        "TDM_FNF50",
        "TREE_CANOPY_COVER_LOSS_P1M",
        "CORINE_LAND_COVER_CHANGE_2000_100x100_ETRS89",
        "CORINE_LAND_COVER_CHANGE_2000_100x100_LAEA",
        "CORINE_LAND_COVER_CHANGE_2006_100x100_ETRS89",
        "CORINE_LAND_COVER_CHANGE_2006_100x100_LAEA",
    ]

    # Iterate over the layers and print their metadata
    items = []
    for layer_name, layer in wms.contents.items():
        try: #if time series skip
            print(layer.dimensions['time'] ) 
        except:
            if layer_name not in not_of_interest:
                item = {}
                item['name'] = layer_name
                item['abstract'] = layer.abstract
                item['width'] = 1000
                item['height'] = 1000
                items.append(item)

    eoc_land = {
        "type": "wms",
        "source": "EOC_Land_Map_Service",
        "file": "EOC_Land_Map_Service.json",
        "link": "https://geoservice.dlr.de/eoc/land/wms",
        "format": "image/geotiff",
        "crs":"EPSG:4326",
        "variables":items,
    }

    # Write to a text file
    with open('EOC_Land_Map_Service.json', 'w') as file:
        json.dump(eoc_land, file, indent=4)