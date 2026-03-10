
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
  <a href="https://doi.org/10.5281/zenodo.17394137"><img src="https://img.shields.io/badge/DOI-10.5281%2Fzenodo.17394137-blue?style=flat-square&logo=Zenodo&logoColor=white" alt="DOI: 10.5281/zenodo.17394137" style="display: inline-block;"></a>

</p>

---

## **Content**

- [Introduction](#introduction)
- [blastdbbuilder](#blastdbbuilder)
- [Features](#features)
- [User Manuals](#user-manuals)
  - [Pre-requisite](#pre-requisite)
  - [Command Line Interface (CLI)](#command-line-interface-cli)
  - [Graphical User Interface (GUI)](#graphical-user-interface-gui)
  - [Windows (WSL) Usage](#windows-wsl-usage)
  - [High Performance Computing (HPC)](#high-performance-computing-hpc)
- [Citation](#citation)
- [Support](#support)

---

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
every book is precisely indexed--- smaller in volume, faster to search,
and more focused in results.

However, manually constructing a custom database from numerous genomes
is tedious, error-prone, and frequently interrupted by the "Duplicate ID
Found" error--- with little guidance available on how to resolve it.

To bridge this gap, I developed the blastdbbuilder package --- an
automated solution for genome download, curation, and database
construction. It eliminates common errors, ensures reproducibility, and
delivers an optimized, high-quality BLASTn database tailored for
diagnostics, biosecurity surveillance, microbial research, and any study
that relies on robust sequence comparison.

---

## **blastdbbuilder**

`blastdbbuilder` is a lightweight toolkit that automates the complete
**BLASTn database preparation workflow**. It streamlines every step ---
from downloading user-specified genomes and organizing datasets to
building **optimized, up-to-date BLASTn databases**.

Designed for **researchers and clinicians**, it provides a
**reproducible, portable, and regularly updated solution** for
constructing BLASTn databases **without manual setup**.

The toolkit leverages:

-   **Singularity / Apptainer containers**
-   **Modular scripts**
-   **Automated genome retrieval from NCBI**

This enables:

-   **Easy deployment across diverse computational environments**
-   **Minimal dependency installation**
-   **Reproducible database generation**
-   **Automatic cleanup of intermediate files**, retaining only the
    final BLASTn database to significantly reduce disk space
    requirements

All genomes are retrieved directly from **NCBI RefSeq repositories**,
ensuring that the database reflects the **latest available sequences at
the time of download**.

---

## **Features**

-   Automated download of all genomes for virus and the reference
    genomes for Archaea, Bacteria, Fungi, and Plants

-   Resume-able BLASTn database creation --- continue from interrupted
    runs

-   Modular scripts for each workflow step

-   Container-based execution for portability and reproducibility

-   Lightweight installation

-   Reduced disk space usage through automatic cleanup of intermediate
    files

---

## **User Manuals**

blastdbbuilder supports multiple user workflows depending on computational environment and user preference. Separate user manuals are provided for each supported usage environment.

### **Pre-requisite**

**System requirements**

Before installing `blastdbbuilder`, make sure the following are
available on your system:

**Python ≥ 3.9**

Check your Python version:

```
python3 --version
```

If Python is older than 3.9, install a newer Python using your system
package manager.

Example (Ubuntu):

```
sudo apt install python3
```


**unzip**

Check if installed:

```
unzip -v
```

If missing:

```
sudo apt install unzip
```


**Container engine**

One of the following container engines must be installed:

-   Apptainer
-   SingularityCE ≥ 3.x

Example installation:

```
sudo apt install singularity-container
```

On most HPC systems (for example ARDC Nectar), Singularity or Apptainer
is typically already installed.

---

### **Command Line Interface (CLI)**

The CLI provides the full automated workflow for downloading genomes,
concatenating FASTA files, and building BLAST databases.

👉 [**CLI User Guide**](https://github.com/asadprodhan/blastdbbuilder/blob/main/docs/CLI_README.md)

---

### **Graphical User Interface (GUI)**

The GUI provides a guided desktop interface for building customised
BLASTn databases without requiring command-line experience.

It wraps the same reproducible backend as the CLI while offering an
interactive environment suitable for diagnostics laboratories, teaching
environments, and routine analyses.

👉 [**GUI User Guide**](https://github.com/asadprodhan/blastdbbuilder/blob/main/docs/GUI_README.md)

---

### **Windows (WSL) Usage**

blastdbbuilder can be run on Windows using **Windows Subsystem for Linux
(WSL)**, enabling Windows users to build BLAST databases locally while
using a Linux backend.


👉 [**WSL User Guide**](https://github.com/asadprodhan/blastdbbuilder/blob/main/docs/WSL_GUI_README.md)

---

### **High Performance Computing (HPC)**

blastdbbuilder is designed to scale efficiently on HPC systems.

It supports:

-   SLURM-based execution
-   containerised workflows
-   large-scale genome downloads


👉 [**HPC User Guide**](https://github.com/asadprodhan/blastdbbuilder/blob/main/docs/HPC_README.md)

---

## **Citation**

Cite this repository

If you use this software in your work, please cite it as follows:

**Prodhan, M. A.** (2025). blastdbbuilder: Building a Customised BLASTn
Database. https://doi.org/10.5281/zenodo.17394137

---

## **Support**

For issues, bug reports, or feature requests, please contact: **Asad
Prodhan. E-mail: asad.prodhan@dpird.wa.gov.au, prodhan82@gmail.com**
