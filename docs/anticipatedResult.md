# Anticipated result

The workflow automatically downloads all required geospatial data files into the directory specified in the general configuration file (**config/config.json**). For each file retrieved, a corresponding log file is generated during execution, providing detailed information about the download process. These log files are essential for monitoring progress and diagnosing potential issues.

In cases where the workflow fails — most commonly due to temporary unavailability of external data services — users should consult the relevant log files to identify the source of the problem. Once resolved, the workflow can be safely restarted, and it will resume from where it left off.

Note that certain issues, such as insufficient storage space or network connectivity problems, must be resolved manually. These fall outside the scope of automated recovery and require user intervention before the workflow can continue successfully.

![Diagram](filesystem.png)