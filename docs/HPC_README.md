
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
  <a href="https://doi.org/10.5281/zenodo.17394137"><img src="https://img.shields.io/badge/DOI-10.5281%2Fzenodo.17394137-blue?style=flat-square&logo=Zenodo&logoColor=white" alt="DOI: 10.5281/zenodo.17394137" style="display: inline-block;"></a>

</p>


## **Content**

<img src="https://raw.githubusercontent.com/asadprodhan/blastdbbuilder/main/blastdbbuilder_logo.png"
     width="190"
     align="right">
     
- [Introduction](#introduction)  
- [Features](#features)  
- [Running blastdbbuilder on HPC clusters](#running-blastdbbuilder-on-hpc-clusters)  
- [Pre-requisite](#pre-requisite)  
- [How to use blastdbbuilder on HPC](#how-to-use-blastdbbuilder-on-hpc)  
- [Step 1 — Download genomes](#step-1--download-genomes)  
- [Step 2 — Concatenate genomes](#step-2--concatenate-genomes)  
- [Step 3 — Build BLAST database](#step-3--build-blast-database)  
- [Final output files](#final-output-files)  
- [Full workflow diagram](#full-workflow-diagram)  
- [Citation](#citation)  
- [Support](#support)


## **Introduction**

A BLASTn database provides the essential reference framework for comparing query sequences, forming the backbone of any sequence-based analysis. Accurate results—whether in diagnostics, biosecurity surveillance, microbial studies, evolutionary research, environmental surveys, or functional genomics—depend on a high-quality, well-curated database.

Public databases are comprehensive but rapidly expanding, often containing redundant, low-quality or irrelevant entries. This leads to slower searches and reduced search resolution.

In contrast, a custom database is like a well-organised library where every book is precisely indexed—smaller in volume, faster to search, and more focused in results.

To simplify this process, **blastdbbuilder** provides an automated command-line workflow for downloading genomes, concatenating FASTA files, and constructing custom BLAST databases in a reproducible manner.

---

## **Features**

- Automated download of RefSeq genomes from NCBI
- FASTA concatenation into a unified reference dataset
- Automated construction of BLAST nucleotide databases
- Fully reproducible workflow using containerised runtime
- Compatible with HPC clusters using SLURM
- No manual dependency installation required

---


## **Running blastdbbuilder on HPC clusters**

High‑performance computing (HPC) clusters provide the computational power required to build large custom BLAST databases efficiently. `blastdbbuilder` can be run on HPC using the **blastdbbuilder container** that allows the entire pipeline to run without installing any dependencies on the cluster.


## **Pre-requisite**

The container bundles all required softwares to run `blastdbbuilder' on HPC:

| Tool | Purpose |
|:-----|:--------|
| blastdbbuilder | Pipeline orchestration |
| NCBI datasets CLI | Genome download |
| dataformat | Metadata parsing |
| BLAST+ | BLAST database construction |
| seqkit | FASTA processing |
| unzip | Genome archive extraction |

This eliminates the need to install:

- BLAST+
- datasets CLI
- seqkit
- additional Python tools

on the HPC system.


---

## **How to use `blastdbbuilder` on HPC**


The pipeline is executed in **three independent stages**.

1. Download genomes  
2. Concatenate FASTA files  
3. Build BLAST database  

Each stage is submitted as a **separate SLURM job**.

---

## **Step 1 — Download genomes**

Example SLURM script:

```
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

**Submit job:**

```
sbatch blastdbbuilder_container_archaea_download_slurm.sh
```

---

## **Step 2 — Concatenate genomes**

```
#!/bin/bash --login
#SBATCH --job-name=blastdbbuilder-archaea-download
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

**Submit job:**

```
sbatch blastdbbuilder_container_concat_slurm.sh
```

---

# **Step 3 — Build BLAST database**

```
#!/bin/bash --login
#SBATCH --job-name=blastdbbuilder-archaea-download
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

**Submit job:**

```
sbatch blastdbbuilder_container_build_slurm.sh
```

---

## **Final output files**

After completion you will obtain:

```
blastnDB/
├── nt.nhr
├── nt.nin
├── nt.nsq
├── nt.ndb
├── nt.njs
├── nt.not
├── nt.ntf
└── nt.nto
```

This is the **final BLAST nucleotide database**.

**Example usage:**

```
blastn -query query.fasta -db blastnDB/nt
```

---

## **Full workflow diagram**

```
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
| Step 1: Download genomes (NCBI RefSeq)     |
+-------------------------------------+
               |
               v
+-------------------------------------+
| Step 2: Concatenate FASTA sequences |
+-------------------------------------+
               |
               v
+-------------------------------------+
| Step 3: Build BLAST database        |
+-------------------------------------+
               |
               v
+-------------------------------------+
|         blastnDB/ directory         |
|  nt.nhr  nt.nin  nt.nsq  nt.ndb     |
+-------------------------------------+
```

---

## **Citation**

If you use this software in your work, please cite:

Prodhan, M. A. (2025). blastdbbuilder: Building a Customised BLASTn Database. https://doi.org/10.5281/zenodo.17394137

---

## **Support**

For issues, bug reports, or feature requests, please contact:

**Asad Prodhan**  
E-mail: asad.prodhan@dpird.wa.gov.au, prodhan82@gmail.com
