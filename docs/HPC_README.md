<h1 align="center">blastdbbuilder on HPC Systems: Container-Based Workflow</h1>

<h3 align="center">M. Asaduzzaman Prodhan<sup>*</sup></h3>

<div align="center"><b> DPIRD Diagnostics and Laboratory Services </b></div>
<div align="center"><b> Department of Primary Industries and Regional Development </b></div>
<div align="center"><b> 31 Cedric St, Stirling WA 6021, Australia </b></div>
<div align="center"><b> *Correspondence: asad.prodhan@dpird.wa.gov.au; prodhan82@gmail.com </b></div>

<br />

<p align="center">
  <a href="https://github.com/asadprodhan/blastdbbuilder/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-GPL%203.0-yellow.svg" alt="License GPL 3.0" style="display: inline-block;"></a>
  <a href="https://orcid.org/0000-0002-1320-3486"><img src="https://img.shields.io/badge/ORCID-green?style=flat-square&logo=ORCID&logoColor=white" alt="ORCID" style="display: inline-block;"></a>
  <a href="https://doi.org/10.5281/zenodo.18973405"><img src="https://img.shields.io/badge/DOI-10.5281%2Fzenodo.18973405-blue?style=flat-square&logo=Zenodo&logoColor=white" alt="DOI: 10.5281/zenodo.18973405" style="display: inline-block;"></a>
</p>


## **Content**

<img src="https://raw.githubusercontent.com/asadprodhan/blastdbbuilder/main/blastdbbuilder_logo.png"
     width="190"
     align="right">

- [Introduction](#introduction)
- [Features](#features)
- [Running blastdbbuilder on HPC clusters](#running-blastdbbuilder-on-hpc-clusters)
- [Pre-requisite](#pre-requisite)
- [Workflow 1. Build from NCBI Reference Genomes](#workflow-1-build-from-ncbi-reference-genomes)
  - [Step 1. Download Genomes](#step-1-download-genomes)
  - [Step 2. Concatenate Genomes](#step-2-concatenate-genomes)
  - [Step 3. Build BLAST Database](#step-3-build-blast-database)
- [Workflow 2. Build from Local FASTA Files](#workflow-2-build-from-local-fasta-files)
- [Final Output Files](#final-output-files)
- [Full Workflow Diagram](#full-workflow-diagram)
- [Citation](#citation)
- [Support](#support)


## **Introduction**

A BLASTn database provides the essential reference framework for
comparing query sequences, forming the backbone of any sequence-based
analysis. Accurate results---whether in diagnostics, biosecurity
surveillance, microbial studies, evolutionary research, environmental
surveys, or functional genomics---depend on a high-quality, well-curated
database.

Public databases are comprehensive but rapidly expanding, often
containing redundant, low-quality, or irrelevant entries. This leads to
slower searches and reduced search resolution.

In contrast, a custom database is like a well-organised library where
every book is precisely indexed---smaller in volume, faster to search,
and more focused in results.

`blastdbbuilder` provides an automated command-line workflow for
constructing customised BLASTn databases in a reproducible manner.
Version 1.2.0 supports both NCBI reference-genome workflows and direct
database construction from local FASTA collections.

---


## **Features**

-   Automated download of all genomes for virus and the reference
    genomes for Archaea, Bacteria, Fungi, and Plants

-   Build customised BLASTn databases directly from local FASTA files
    (`.fasta`, `.fa`, `.fna`, and `.fas`)

-   Automatic handling of local FASTA collections --- use a single
    FASTA directly or concatenate multiple FASTA files before database
    construction

-   FASTA concatenation into a unified reference dataset

-   Automated construction of BLASTn databases

-   Reproducible container-based execution

-   Compatible with HPC clusters using SLURM

-   No manual installation of the container-bundled bioinformatics
    dependencies

---


## **Running blastdbbuilder on HPC clusters**

High-performance computing (HPC) clusters provide the storage and
computational resources required to build large customised BLASTn
databases efficiently.

`blastdbbuilder` can be run on HPC using the **blastdbbuilder
container**, allowing the workflow and its bioinformatics dependencies
to execute in a reproducible containerised environment.

The examples below use **Singularity** and **SLURM**. Cluster module
names, accounts, partitions, storage paths, and resource requests vary
between HPC systems and should be adjusted for the target cluster.

---


## **Pre-requisite**

The blastdbbuilder container bundles the software required by the
workflow:

| Tool | Purpose |
|:-----|:--------|
| blastdbbuilder | Workflow orchestration |
| NCBI datasets CLI | Genome download |
| dataformat | Metadata processing |
| BLAST+ | BLASTn database construction |
| seqkit | FASTA processing |
| unzip | Genome archive extraction |

The HPC system must provide a compatible **Singularity/Apptainer
runtime**.

For the examples below, SLURM is also required for job submission.

---


## **Workflow 1. Build from NCBI Reference Genomes**

The NCBI reference-genome workflow is executed in three independent
stages:

1. Download genomes
2. Concatenate FASTA files
3. Build the BLASTn database

Each stage can be submitted as a separate SLURM job.

The scripts below retain the container version used in the existing HPC
workflow example (`v1.0.3`). If using a newer blastdbbuilder container,
update both `CONTAINER` and `IMAGE_URI` to the corresponding published
container tag.

### **Step 1. Download Genomes**

Example SLURM script:

```bash
#!/bin/bash --login
#SBATCH --job-name=blastdbbuilder-archaea-download
#SBATCH --account=xxx
#SBATCH --partition=xxx
#SBATCH --time=04:00:00
#SBATCH --ntasks=1
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --output=blastdbbuilder_archaea_download_%j.out
#SBATCH --error=blastdbbuilder_archaea_download_%j.err
#SBATCH --export=NONE

set -euo pipefail
unset SLURM_EXPORT_ENV

module load singularity/4.1.0-slurm

BASE="$MYSCRATCH"

WORKDIR="${BASE}/blastdbbuilder_archaea_test"
CONTAINER_DIR="${BASE}/containers"
CONTAINER="${CONTAINER_DIR}/blastdbbuilder_v1.0.3.sif"

IMAGE_URI="docker://quay.io/asadprodhan/blastdbbuilder:v1.0.3"

export SINGULARITY_CACHEDIR="${BASE}/.singularity/cache"
export SINGULARITY_TMPDIR="${BASE}/.singularity/tmp/${SLURM_JOB_ID}"

mkdir -p "$WORKDIR" "$CONTAINER_DIR" "$SINGULARITY_CACHEDIR" "$SINGULARITY_TMPDIR"

cd "$WORKDIR"

if [ ! -f "$CONTAINER" ]; then
    singularity pull "$CONTAINER" "$IMAGE_URI"
fi

singularity exec \
  --bind "$WORKDIR":"$WORKDIR" \
  --pwd "$WORKDIR" \
  "$CONTAINER" \
  blastdbbuilder --download --archaea
```

Submit:

```bash
sbatch blastdbbuilder_container_archaea_download_slurm.sh
```

---


### **Step 2. Concatenate Genomes**

Example SLURM script:

```bash
#!/bin/bash --login
#SBATCH --job-name=blastdbbuilder-archaea-concat
#SBATCH --account=xxx
#SBATCH --partition=xxx
#SBATCH --time=04:00:00
#SBATCH --ntasks=1
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --output=blastdbbuilder_archaea_concat_%j.out
#SBATCH --error=blastdbbuilder_archaea_concat_%j.err
#SBATCH --export=NONE

set -euo pipefail
unset SLURM_EXPORT_ENV

module load singularity/4.1.0-slurm

BASE="$MYSCRATCH"

WORKDIR="${BASE}/blastdbbuilder_archaea_test"
CONTAINER_DIR="${BASE}/containers"
CONTAINER="${CONTAINER_DIR}/blastdbbuilder_v1.0.3.sif"

IMAGE_URI="docker://quay.io/asadprodhan/blastdbbuilder:v1.0.3"

export SINGULARITY_CACHEDIR="${BASE}/.singularity/cache"
export SINGULARITY_TMPDIR="${BASE}/.singularity/tmp/${SLURM_JOB_ID}"

mkdir -p "$WORKDIR" "$CONTAINER_DIR" "$SINGULARITY_CACHEDIR" "$SINGULARITY_TMPDIR"

cd "$WORKDIR"

if [ ! -f "$CONTAINER" ]; then
    singularity pull "$CONTAINER" "$IMAGE_URI"
fi

singularity exec \
  --bind "$WORKDIR":"$WORKDIR" \
  --pwd "$WORKDIR" \
  "$CONTAINER" \
  blastdbbuilder --concat
```

Submit:

```bash
sbatch blastdbbuilder_container_concat_slurm.sh
```

---


### **Step 3. Build BLAST Database**

Example SLURM script:

```bash
#!/bin/bash --login
#SBATCH --job-name=blastdbbuilder-archaea-build
#SBATCH --account=xxx
#SBATCH --partition=xxx
#SBATCH --time=04:00:00
#SBATCH --ntasks=1
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --output=blastdbbuilder_archaea_build_%j.out
#SBATCH --error=blastdbbuilder_archaea_build_%j.err
#SBATCH --export=NONE

set -euo pipefail
unset SLURM_EXPORT_ENV

module load singularity/4.1.0-slurm

BASE="$MYSCRATCH"

WORKDIR="${BASE}/blastdbbuilder_archaea_test"
CONTAINER_DIR="${BASE}/containers"
CONTAINER="${CONTAINER_DIR}/blastdbbuilder_v1.0.3.sif"

IMAGE_URI="docker://quay.io/asadprodhan/blastdbbuilder:v1.0.3"

export SINGULARITY_CACHEDIR="${BASE}/.singularity/cache"
export SINGULARITY_TMPDIR="${BASE}/.singularity/tmp/${SLURM_JOB_ID}"

mkdir -p "$WORKDIR" "$CONTAINER_DIR" "$SINGULARITY_CACHEDIR" "$SINGULARITY_TMPDIR"

cd "$WORKDIR"

if [ ! -f "$CONTAINER" ]; then
    singularity pull "$CONTAINER" "$IMAGE_URI"
fi

singularity exec \
  --bind "$WORKDIR":"$WORKDIR" \
  --pwd "$WORKDIR" \
  "$CONTAINER" \
  blastdbbuilder --build
```

Submit:

```bash
sbatch blastdbbuilder_container_build_slurm.sh
```

---


## **Workflow 2. Build from Local FASTA Files**

Version 1.2.0 also supports building a BLASTn database directly from a
directory containing local FASTA files.

Supported extensions are:

-   `.fasta`
-   `.fa`
-   `.fna`
-   `.fas`

The CLI command is:

```bash
blastdbbuilder --build --input-dir /path/to/fasta_directory
```

If the directory contains one supported FASTA file, that file is used
directly. If multiple supported FASTA files are present, they are
concatenated before database construction. The original FASTA files are
preserved.

On an HPC system, the FASTA directory must be visible inside the
container. A typical SLURM pattern is:

```bash
#!/bin/bash --login
#SBATCH --job-name=blastdbbuilder-local-fasta
#SBATCH --account=xxx
#SBATCH --partition=xxx
#SBATCH --time=04:00:00
#SBATCH --ntasks=1
#SBATCH --nodes=1
#SBATCH --cpus-per-task=4
#SBATCH --mem=16G
#SBATCH --output=blastdbbuilder_local_fasta_%j.out
#SBATCH --error=blastdbbuilder_local_fasta_%j.err
#SBATCH --export=NONE

set -euo pipefail
unset SLURM_EXPORT_ENV

module load singularity/4.1.0-slurm

BASE="$MYSCRATCH"

WORKDIR="${BASE}/blastdbbuilder_local_test"
FASTA_DIR="${WORKDIR}/fasta"
CONTAINER_DIR="${BASE}/containers"

# Use a blastdbbuilder container release that includes v1.2.0 local
# FASTA support.
CONTAINER="${CONTAINER_DIR}/blastdbbuilder_v1.2.0.sif"
IMAGE_URI="docker://quay.io/asadprodhan/blastdbbuilder:v1.2.0"

export SINGULARITY_CACHEDIR="${BASE}/.singularity/cache"
export SINGULARITY_TMPDIR="${BASE}/.singularity/tmp/${SLURM_JOB_ID}"

mkdir -p "$WORKDIR" "$FASTA_DIR" "$CONTAINER_DIR" \
         "$SINGULARITY_CACHEDIR" "$SINGULARITY_TMPDIR"

cd "$WORKDIR"

if [ ! -f "$CONTAINER" ]; then
    singularity pull "$CONTAINER" "$IMAGE_URI"
fi

singularity exec \
  --bind "$WORKDIR":"$WORKDIR" \
  --pwd "$WORKDIR" \
  "$CONTAINER" \
  blastdbbuilder --build --input-dir "$FASTA_DIR"
```

> **Important:** the `v1.2.0` container tag in this example must exist in
> the container registry before this script is used. If the container
> has not yet been released at v1.2.0, build or publish the updated
> container first rather than using the older v1.0.3 image for the new
> `--input-dir` workflow.

Submit:

```bash
sbatch blastdbbuilder_container_local_fasta_slurm.sh
```

---


## **Final Output Files**

After successful database construction, the final database is written
under:

```text
blastnDB/nt.*
```

Depending on the BLAST+ database format/version used by the container,
the `blastnDB` directory contains the nucleotide database files required
by BLASTn.

Example usage:

```bash
blastn -query query.fasta -db blastnDB/nt
```

---


## **Full Workflow Diagram**

```text
+-----------------------------+
|      HPC Cluster (SLURM)    |
+-----------------------------+
               |
               v
+-------------------------------------+
|  blastdbbuilder container runtime   |
+-------------------------------------+
               |
               v
+-------------------------------------+
|      Select input workflow          |
+-------------------------------------+
        |                     |
        v                     v
+------------------+   +----------------------+
| NCBI Reference   |   | Local FASTA files    |
| Genomes          |   | .fasta/.fa/.fna/.fas|
+------------------+   +----------------------+
        |                     |
        v                     v
+------------------+   +----------------------+
| Download genomes |   | Use one FASTA or     |
+------------------+   | concatenate multiple |
        |              +----------------------+
        v                     |
+------------------+          |
| Concatenate      |          |
| FASTA sequences  |          |
+------------------+          |
        |                     |
        +----------+----------+
                   |
                   v
+-------------------------------------+
|      Build BLASTn database          |
+-------------------------------------+
                   |
                   v
+-------------------------------------+
|          blastnDB/nt.*              |
+-------------------------------------+
```

---


## **Citation**

If you use this software in your work, please cite:

**Prodhan, M. A.** (2025). blastdbbuilder: Building a Customised BLASTn
Database. https://doi.org/10.5281/zenodo.18973405

---


## **Support**

For issues, bug reports, or feature requests, please contact:

**Asad Prodhan**  
E-mail: asad.prodhan@dpird.wa.gov.au, prodhan82@gmail.com
