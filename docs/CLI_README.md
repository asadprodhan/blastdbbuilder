<h1 align="center">blastdbbuilder: Building a Customised BLASTn Database</h1>


<h3 align="center">M. Asaduzzaman Prodhan<sup>*</sup> </h3>


<div align="center"><b> DPIRD Diagnostics and Laboratory Services </b></div>


<div align="center"><b> Department of Primary Industries and Regional Development </b></div>


<div align="center"><b> 3 Baron-Hay Court, South Perth, WA 6151, Australia </b></div>


<div align="center"><b> *Correspondence: asad.prodhan@dpird.wa.gov.au; prodhan82@gmail.com </b></div>


<br />


<p align="center">
  <a href="https://github.com/asadprodhan/blastdbbuilder/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-GPL%203.0-yellow.svg" alt="License GPL 3.0" style="display: inline-block;"></a>
  <a href="https://orcid.org/0000-0002-1320-3486"><img src="https://img.shields.io/badge/ORCID-green?style=flat-square&logo=ORCID&logoColor=white" alt="ORCID" style="display: inline-block;"></a>
  <a href="https://doi.org/10.5281/zenodo.18973405"><img src="https://img.shields.io/badge/DOI-10.5281%2Fzenodo.18973405-blue?style=flat-square&logo=Zenodo&logoColor=white" alt="DOI: 10.5281/zenodo.18973405" style="display: inline-block;">

</p>

## **Content**

<img src="https://raw.githubusercontent.com/asadprodhan/blastdbbuilder/main/blastdbbuilder_logo.png"
     width="190"
     align="right">

- [Introduction](#introduction)
- [blastdbbuilder](#blastdbbuilder)
- [Features](#features)
- [Pre-requisite](#pre-requisite)
- [Installation](#installation)
- [Usage](#usage)
  - [Workflow 1. Build from NCBI Reference Genomes](#workflow-1-build-from-ncbi-reference-genomes)
    - [Step 1. Download Genomes](#step-1-download-genomes)
    - [Step 2. Concatenate Genomes](#step-2-concatenate-genomes)
    - [Step 3. Build BLAST Database](#step-3-build-blast-database)
  - [Workflow 2. Build from Local FASTA Files](#workflow-2-build-from-local-fasta-files)
  - [Final Files](#final-files)
- [Citation](#citation)
- [Support](#support)


## **Introduction**

A BLASTn database provides the essential reference framework for
comparing query sequences, forming the backbone of any sequence-based
analysis. Accurate results---whether in diagnostics, biosecurity
surveillance, microbial studies, evolutionary research, environmental
surveys, or functional genomics---depend on a high-quality, well-curated
database; without it, even the most sophisticated tools can yield
ambiguous outcomes.

Public databases are comprehensive but rapidly expanding, often
containing redundant or low-quality and irrelevant entries. This leads
to slower searches and reduced search resolution.

In contrast, a custom database is like a well-organised library where
every book is precisely indexed---smaller in volume, faster to search,
and more focused in results.

However, manually constructing a custom database from numerous genomes
is tedious, error-prone, and frequently interrupted by the "Duplicate ID
Found" error---with little guidance available on how to resolve it.

To bridge this gap, I developed the `blastdbbuilder` package---an
automated solution for genome download, curation, and database
construction. Version 1.2.0 additionally supports building customised
BLASTn databases directly from local FASTA collections.

---


## **blastdbbuilder**

`blastdbbuilder` is a lightweight command-line toolkit that automates
the **BLASTn database preparation workflow**.

It supports two database-building workflows:

-   **NCBI Reference Genomes** --- download selected genome collections,
    concatenate the FASTA files, and build a customised BLASTn database

-   **Local FASTA Files** --- build a customised BLASTn database directly
    from your own `.fasta`, `.fa`, `.fna`, or `.fas` files

For local FASTA collections, a single FASTA file can be used directly,
while multiple FASTA files can be concatenated before database
construction.

The toolkit uses container-based execution and modular workflow scripts
to provide portable and reproducible database generation across
different computational environments.

---


## **Features**

-   Automated download of all genomes for virus and the reference
    genomes for Archaea, Bacteria, Fungi, and Plants

-   Build custom BLASTn databases directly from local FASTA files
    (`.fasta`, `.fa`, `.fna`, and `.fas`)

-   Automatic handling of local FASTA collections --- use a single
    FASTA directly or concatenate multiple FASTA files before database
    construction

-   Resume-able BLASTn database creation --- continue from interrupted
    runs

-   Modular scripts for each workflow step

-   Container-based execution for portability and reproducibility

-   Lightweight installation

-   Reduced disk space usage through automatic cleanup of intermediate
    files

---


## **Pre-requisite**

**System requirements**

Before installing `blastdbbuilder`, make sure the following are
available on your system:

**Python ≥ 3.9**

Check your Python version:

```bash
python3 --version
```

If Python is older than 3.9, install a newer Python using your system
package manager.

Example (Ubuntu):

```bash
sudo apt install python3
```

**unzip**

The program requires the `unzip` utility to extract downloaded genome
archives.

Check if installed:

```bash
unzip -v
```

If missing:

```bash
sudo apt install unzip
```

**Container engine**

One of the following container engines must be installed:

-   Apptainer
-   SingularityCE ≥ 3.x

Example installation on Ubuntu / Debian:

```bash
sudo apt install singularity-container
```

The program automatically detects which supported container engine is
available and uses it.

On many HPC systems, Singularity or Apptainer is typically already
installed.

---


## **Installation**

Install `blastdbbuilder` directly from PyPI:

```bash
pip install blastdbbuilder
```

To upgrade an existing installation:

```bash
pip install --upgrade blastdbbuilder
```

Verify the installation:

```bash
blastdbbuilder --help
```

Check the installed version:

```bash
blastdbbuilder --version
```

The v1.2.0 CLI includes the existing download, concatenate, and build
operations together with local FASTA directory support through
`--input-dir`.

**Optional: Install from GitHub (development version)**

Clone the repository and install the CLI package:

```bash
git clone https://github.com/asadprodhan/blastdbbuilder.git
cd blastdbbuilder/cli
pip install -e .
```

To uninstall:

```bash
pip uninstall blastdbbuilder -y
```

---


## **Usage**

`blastdbbuilder` provides two ways to create a customised BLASTn
database.

### **Workflow 1. Build from NCBI Reference Genomes**

This workflow downloads selected genome groups, concatenates the
downloaded FASTA files, and builds the BLASTn database.

Open a terminal and choose a working directory with sufficient storage.

For example:

```bash
mkdir abfvp
cd abfvp
```

Run the following three steps sequentially.

### **Step 1. Download Genomes**

Download Archaea genomes:

```bash
blastdbbuilder --download --archaea
```

Download Bacteria genomes:

```bash
blastdbbuilder --download --bacteria
```

Download Fungal genomes:

```bash
blastdbbuilder --download --fungi
```

Download Viral genomes:

```bash
blastdbbuilder --download --virus
```

Download Plant genomes:

```bash
blastdbbuilder --download --plants
```

Multiple groups can be selected in the same command. For example:

```bash
blastdbbuilder --download --archaea --bacteria
```

Or:

```bash
blastdbbuilder --download --archaea --bacteria --fungi --virus --plants
```

### **Step 2. Concatenate Genomes**

After downloading the selected genomes, run:

```bash
blastdbbuilder --concat
```

This concatenates the downloaded genome FASTA files for database
construction.

### **Step 3. Build BLAST Database**

Build the BLASTn database:

```bash
blastdbbuilder --build
```

The database is written to the `blastnDB` directory.

---


### **Workflow 2. Build from Local FASTA Files**

Version 1.2.0 allows a BLASTn database to be built directly from a
directory containing your own FASTA files.

Supported extensions are:

-   `.fasta`
-   `.fa`
-   `.fna`
-   `.fas`

To build directly from a FASTA directory:

```bash
blastdbbuilder --build --input-dir /path/to/fasta_directory
```

If the directory contains a single supported FASTA file, that file is
used directly for database construction.

If the directory contains multiple supported FASTA files, they are
concatenated before the database is built.

The original FASTA files are preserved.

The resulting BLASTn database is written to:

```text
blastnDB/nt.*
```

---


### **Final Files**

After database construction, the final BLASTn database is available in:

```text
blastnDB/
```

The directory contains the BLASTn database files with the `nt` database
prefix.

**You have now created your customised BLASTn database. The database is
portable and can be moved to another compatible computer or analysis
environment for use with BLASTn.**

---


## **Citation**

Cite this repository

If you use this software in your work, please cite it as follows:

**Prodhan, M. A.** (2025). blastdbbuilder: Building a Customised BLASTn
Database. https://doi.org/10.5281/zenodo.18973405

---


## **Support**

For issues, bug reports, or feature requests, please contact:
**Asad Prodhan. E-mail: asad.prodhan@dpird.wa.gov.au,
prodhan82@gmail.com**
