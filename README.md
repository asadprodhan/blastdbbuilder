
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

<br />

## **Content**

- [Introduction](#introduction)
- [blastdbbuilder](#blastdbbuilder)
- [Features](#features)
- [Pre-requisite](#pre-requisite)
- [Installation](#installation)
- [Usage](#usage)
  - [Step 1. Download Genomes](#step-1-download-genomes)  
  - [Step 2. Concatenate Genomes](#step-2-concatenate-genomes)
  - [Step 3. Build BLAST Database](#step-3-build-blast-database)
  - [Final Files](#final-files)
- [Citation](#citation)
- [Support](#support)


<br />


## **Introduction**

A BLASTn database provides the essential reference framework for comparing query sequences, forming the backbone of any sequence-based analysis. Accurate results—whether in diagnostics, biosecurity surveillance, microbial studies, evolutionary research, environmental surveys, or functional genomics—depend on a high-quality, well-curated database; without it, even the most sophisticated tools can yield ambiguous outcomes.

Public databases are comprehensive but rapidly expanding, often containing redundant or low-quality and irrelevant entries. This leads to slower searches and reduced search resolution. 

In contrast, a custom database is like a well-organised library where every book is precisely indexed— smaller in volume, faster to search, and more focused in results.

However, manually constructing a custom database from numerous genomes is tedious, error-prone, and frequently interrupted by the “Duplicate ID Found” error— with little guidance available on how to resolve it.

To bridge this gap, I developed the blastdbbuilder package — an automated solution for genome download, curation, and database construction. It eliminates common errors, ensures reproducibility, and delivers an optimized, high-quality BLASTn database tailored for diagnostics, biosecurity surveillance, microbial research, and any study that relies on robust sequence comparison.

<br />


## **blastdbbuilder Command Line Interface (CLI)**


`blastdbbuilder` is a lightweight, command-line toolkit that automates the complete **BLASTn database preparation workflow**. It streamlines every step — from downloading user-specified genomes and organizing datasets to building **optimized, up-to-date BLASTn databases**.

Designed for **researchers and clinicians**, it provides a **reproducible, portable, and regularly updated solution** for constructing BLASTn databases **without manual setup**.

The toolkit leverages:  
- **Singularity containers**  
- **Modular shell scripts**  

Which enables:  
- **Easy deployment** across diverse computational environments  
- **No dependency installation**  
- A **smooth and user-friendly experience**  
- **Automatic cleanup of intermediate files**, retaining only the final BLASTn database and **significantly reducing disk space requirements**  

Additionally, `blastdbbuilder` retrieves genomes directly from **NCBI’s FTP servers**, ensuring that all sequences are **as current as the time of download**.


<br />

## **Features**

- Automated download of all genomes for virus and the reference genomes for Archaea, Bacteria, Fungi, and Plants
  
- Resume-able BLASTn database creation — continue from interrupted runs
   
- Modular bash scripts for each task
    
- Use of Singularity containers for less software installation and portability
    
- Lightweight installation 
  
- Less disk space requirement 
 

<br />


## **Pre-requisite**


- Install git

  ```
  conda install anaconda::git
  ```


- Install pip

  ```
  conda install anaconda::pip
  ```

- Install Singularity

  ```
  conda install bioconda::singularity
  ```

  Or,


  ```
  conda install bioconda/label/cf201901::singularity
  ```

<br />


## **Installation**

Clone the GitHub Repository:

  ```
  git clone https://github.com/AsadProdhan/blastdbbuilder.git
  ```

Then, go to the blastdbbuilder directory 

  ```
  cd blastdbbuilder
  ```

Install blastdbbuilder

  ```
  python3 -m pip install --editable .
  ```

Check if the installation has been successful

  ```
  blastdbbuilder --help
  ```

Check the version

  ```
  blastdbbuilder --version
  ```


<br />

### If you see the following usage flags, then 

  - the **installation** has been successful
  
  - you can run ***blastdbbuilder*** from any directory in your computer 



<br />


```
usage: blastdbbuilder [-h] [--download] [--concat] [--build] [--citation] [--archaea] [--bacteria] [--fungi]
                      [--virus] [--plants]

blastdbbuilder: Automated genome download, concatenation, and BLAST database builder

options:
  -h, --help  show this help message and exit
  --download  Download genomes for selected groups
  --concat    Concatenate all genomes into one FASTA
  --build     Build BLAST database from concatenated FASTA
  --citation  Print citation information
  --archaea   Include Archaea genomes
  --bacteria  Include Bacteria genomes
  --fungi     Include Fungi genomes
  --virus     Include Virus genomes (all)
  --plants    Include Plant genomes
```

Close your terminal.


If you want to uninstall blastdbbuilder, run the following command in the same directory where you have installed blastdbbuilder.

  ```
  pip uninstall blastdbbuilder -y
  ```

Check if the uninstallation has been successful

  ```
  blastdbbuilder --help
  ```

Now, you will see an error.


<br />


## Usage

  - There are three steps from downloading the genomes to building a BLASTn database
  
  - Open a terminal
  
  - Make a directory. Name it based on which group/s you are going to download. For example
  

    ```
    mkdir bacteria
    ```   

  - Or, maybe something like this if you are going to download archaea (a), bacteria (b), fungi (f), virus (v), and plants (p). This will help remember what are in the database files which will look like nt.001, nt.002, nt.003 and so on

    ```
    mkdir abfvp
    ```

  - Now cd to that directory


    ```
    cd abfvp
    ```

  - In this directory, run the following three steps- download, concat and build - sequentially
   
<br />


### **Step 1. Download genomes**


Download Archaea genomes

  ```
  blastdbbuilder --download --archaea
  ```

  - This will create an "archaea" directory (db/archaea) and download the  archaeal genomes there. Same for the other groups as well


Download Bacteria genomes

  ```
  blastdbbuilder --download --bacteria
  ```

Download Fungal genomes

  ```
  blastdbbuilder --download --fungi
  ```

Download Viral genomes

  ```
  blastdbbuilder --download --virus
  ```

Download Plant genomes

  ```
  blastdbbuilder --download --plants
  ```

Download multiple groups simultaneously in varius combinations of your interest


  ```
  blastdbbuilder --download --archaea --bacteria 
  ```

  Or,


  ```
  blastdbbuilder --download --archaea --bacteria --fungi --virus --plants
  ```

<br />


### **Step 2. Concatenate genomes**

After downloading, run the following command. 

  ```
  blastdbbuilder --concat
  ```

  - This will create a directory called `concat` and put the concatenated file (containing all the downloaded genomes) in there 

<br />


### **Step 3. Build BLAST database**

Finally, run the following command.

  ```
  blastdbbuilder --build
  ```

  - This will build a BLASTn database from the concatenated FASTA file
    
  - When the run finished, it will clean up all the intermediate files and directories to reduce disk space usage
    
  - You will see only one directory named blastnDB
    
  - blastnDB will contain all the database files, nt.001, nt.002 etc

<br />


### **Final Files**

After running, the directory structure will look like:

  ```
  blastnDB/
  ├─ nt.001.fna.gz
  ├─ nt.002.fna.gz
  ├─ nt.003.fna.gz
  ├─ nt.004.fna.gz
  ├─ nt.nl        
  ├─ logs/
    ├─ nt.001.log
    ├─ nt.002.log
    ├─ nt.003.log
    └─ nt.004.log
  ```

<br />

**You have just created your customised BLASTn database. It is **fully portable**, can be moved to other users/computers and used without making any changes**

<br />

## **blastdbbuilder Graphical User Interface (GUI)**

The blastdbbuilder GUI provides a simple, guided desktop interface for building customised BLASTn databases without requiring command-line experience, making the workflow more accessible for routine diagnostics and research users. It wraps the same reproducible and containerised backend as the CLI, ensuring identical, high-quality database outputs.

👉 **GUI User Manual:** https://github.com/asadprodhan/blastdbbuilder/tree/main/GUI


<br />


## **Citation**

Cite this repository

If you use this software in your work, please cite it as follows:

Prodhan, M. A. (2025). blastdbbuilder: Building a Customised BLASTn Database. https://doi.org/10.5281/zenodo.17394137

<br />

## **Support**

For issues, bug reports, or feature requests, please contact: **Asad Prodhan. E-mail: asad.prodhan@dpird.wa.gov.au, prodhan82@gmail.com**



