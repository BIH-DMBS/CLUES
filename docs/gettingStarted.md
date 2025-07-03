# Getting Started

This guide walks you through setting up your environment and running the CLUES data processing workflow using Snakemake, a workflow management system that automates the execution of data analysis pipelines.

## Prerequisites

Before getting started, ensure the following tools are installed:

- Python 3.8 or higher
- `pip` (Python package manager)
- Git
- [Snakemake](https://snakemake.readthedocs.io/en/stable/)
- (Optional but recommended) `conda` — for reproducible environments

## Setup Instructions

### Clone the Repository

Navigate to your preferred working directory and clone the CLUES repository:

<pre>
git clone https://gitlab.com/bih_dmbs/CLUES/workflows.git
</pre>

### Set up a virtual python environment:

<pre>
python -m venv cluesEnv*
</pre>

**Activate the virtual environment**

Linux/macOS:

<pre>
source cluesEnv/bin/activate
</pre>

Windows:
<pre>
*cluesEnv\Scripts\activate*
</pre>

#### Install dependencies:
Install the required Python packages:

<pre>
pip install -r requirements.txt
</pre>


### Run the workflow
Once everything is set up and the [Third Party Accounts](3rdPartyAccounts.md) are created, you can run the CLUES workflow using Snakemake:

<pre>
snakemake -s workflows/snakefile --cores 16 -p --rerun-incomplete --latency-wait 60
</pre>

Command Options Explained:

- -s workflows/snakefile specifies the Snakefile path

- --cores 16 uses 16 cores for parallel execution

- -p prints out shell commands being executed

- --rerun-incomplete reruns any jobs that were not completed

- --latency-wait 60 waits up to 60 seconds for output files (useful on shared filesystems)

## Next step
Once completed, the required data will be downloaded and stored as specified in your general workflow configuration file (config/config.json). You can then proceed to link environmental data to participant locations using the [Data Linkage Scripts](enrichment.md).
