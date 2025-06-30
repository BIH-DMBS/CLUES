# Getting Started

This guide will help you set up the environment and run the Snakemake workflow for this project.

## Prerequisites

Before you begin, make sure you have the following installed:

- Python 3.8 or higher
- `pip` (Python package manager)
- Git
- [Snakemake](https://snakemake.readthedocs.io/en/stable/)
- (Optional) `conda` — recommended for reproducible environments

## Deployment

### Clone the Repository

Clone this repository to your local machine:
Navigate to the target working directory


<pre>
git clone https://gitlab.com/bih_dmbs/CLUES/workflows.git
</pre>


### Set up a virtual python environment:

<pre>
python -m venv cluesEnv*
</pre>

**Activate virtual environment**

Linux/macOS:

<pre>
source cluesEnv/bin/activate
</pre>

Windows:
<pre>
*cluesEnv\Scripts\activate*
</pre>

#### Install dependicies:

<pre>
pip install -r requirements.txt
</pre>


#### Run snakemake workflow
If all is setup run the workflow:

<pre>
snakemake -s workflows/snakefile --cores 16 -p --rerun-incomplete --latency-wait 60
</pre>

Options Explained:

- -s workflows/snakefile specifies the Snakefile path

- --cores 16 uses 16 cores for parallel execution

- -p prints out shell commands being executed

- --rerun-incomplete reruns any jobs that were not completed

- --latency-wait 60 waits up to 60 seconds for output files (useful on shared filesystems)