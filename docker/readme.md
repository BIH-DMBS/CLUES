# CLUES Docker Usage

This repository provides a Dockerized environment for running **CLUES**.  
The setup ensures a consistent and isolated execution environment without requiring manual installation of dependencies.

---

## Build the Docker Image

Run the following command to build the Docker image locally:

```bash
docker build -t clues .
```

**Configs:** Local config/, configs_sources/, and secrets/ folders are copied into the container.

The the config/ and configs_sources/ contain default files that run as a short demo.

The secrets/ folder must contain the credential files for the copernicus api, nasa earth login and copernicus. The files are given per default but need to be adjusted with personal credentials (check https://bih-dmbs.github.io/CLUES/).


# CLUES with Docker


To run CLUES interactively:

```bash
docker run -it --rm -v ${PWD}/clues_data:/app/CLUES/clues_data clues 
```
This will start the container and starts a bash shell.

To run CLUES start the workflow inside the container with:

```bash
snakemake -s workflows/snakefile --cores 16 -p --scheduler greedy --rerun-incomplete --latency-wait 30
```

The folder clues_data\ set in the config file will be used to store the results. The folder is mirrored on the local mashine.