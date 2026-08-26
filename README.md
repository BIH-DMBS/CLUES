# CLUES: A Comprehensive Workflow for Integrating Geospatial Data in Health Research

## About
CLUES (Climate, Urbanicity, Environment and Society) is a modular workflow that enables researchers to systematically integrate open-access geospatial environmental data with health research datasets at the individual-level. It automates the download, harmonisation, and management of data across climate, built/ natural environment, air pollution, and regional socioeconomic conditions.

Get in touch: dmbs@bih-charite.de  

**Key Features**  

- Automated data retrieval from multiple open-access geospatial sources  
- Standardised harmonisation of spatial/ temporal coverage, projections, and file types  
- Modular integration with health cohort datasets at the individual level  
- Extensible architecture for adding new environmental variables over time  
- Adherence to FAIR (Findable, Accessible, Interoperable, Reusable) and data protection principles  


![Diagram](docs/CLUES_schema.png)

## Getting started
- A extended documentation can be found under [here] (https://bih-dmbs.github.io/CLUES/).
- To understand the scientific foundation of CLUES, please read our [publication](https://doi.org/10.1038/s41467-026-73048-6).  
- To get an overview of the geospatial data and data sources used in CLUES, see the [Data List](docs/data_list.md). For more infomation, visit the [Geospatial Data Guide](docs/dataCatalog.md).  
- To learn how to use the CLUES framework, follow the [User Guide](docs/UserGuide.md) and explore the [Applied Examples](https://github.com/BIH-DMBS/CLUES/blob/main/docs/Examples.md) or the [random forest example](notebooks\random_forest_demo\random_forest_analysis_marseille_summer_school_2025.ipynb).  
- [Scripts](scripts) for integrating the geospatial database to location data and [python notebooks](notebooks) for interacting and visualising the geospatial data are available.  
- For more information on software resources, see [here](docs/softwareResources.md).  

## Citation
Please cite this article:  

Jentsch, M., Polemiti, E., Renner, P. et al. CLUES A Comprehensive Workflow for Integrating Geospatial Data in Biomedical Research. Nat Commun 17, 4330 (2026). 

### DOI  
https://doi.org/10.1038/s41467-026-73048-6

## Maintainers 
The CLUES maintainers are:  

- Marcel Jentsch (lead maintainer)  
- Sven Twardziok  
- Elli Polemiti  

## Usage policies
All datasets used in CLUES are open-access and publicly available, but each comes with its own licensing terms and conditions. We encourage users to review the terms of use for each of them to ensure proper citation and responsible use.  
This includes understanding any limits on redistribution, commercial use, or derivative works.  
You can find an overview of the main data sources and datasets included in the default workflow [here](docs\dataCatalog.md), which can help users identify the relevant licenses to consult as needed.

## License
[MIT License](LICENSE)  
Copyright (c) 2025 BIH-DMBS 

## Past Events

**Date: 24.06.2026**

In this seminar, we presented the CLUES pipeline and demonstrate how environmental exposure data from open-access sources can be systematically linked to individual-level health data in a privacy-compliant way. 

**Link:** https://www.environmental-project.org/resources/environmental-seminar-series/
