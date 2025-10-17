
<h1 align="center">blastdbbuilder: Building a Customised Blastn Database</h1>


<h3 align="center">M. Asaduzzaman Prodhan<sup>*</sup> </h3>


<div align="center"><b> DPIRD Diagnostics and Laboratory Services </b></div>


<div align="center"><b> Department of Primary Industries and Regional Development </b></div>


<div align="center"><b> 3 Baron-Hay Court, South Perth, WA 6151, Australia </b></div>


<div align="center"><b> *Correspondence: prodhan82@gmail.com </b></div>


<br />


<p align="center">
  <a href="https://github.com/asadprodhan/blastdbbuilder/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-GPL%203.0-yellow.svg" alt="License GPL 3.0" style="display: inline-block;"></a>
  <a href="https://orcid.org/0000-0002-1320-3486"><img src="https://img.shields.io/badge/ORCID-green?style=flat-square&logo=ORCID&logoColor=white" alt="ORCID" style="display: inline-block;"></a>
</p>


<br />


## **Introduction**

Reliable sequence-based diagnostics depend on a high-quality, relevant reference database—without it, even the best tools can give misleading results.

In diagnostic workflows, a BLASTn database provides the reference against which query sequences are compared to identify pathogens or assign taxonomy. The quality and composition of the database directly affect accuracy.

Public databases, while comprehensive, often contain redundant sequences, low-quality entries, and irrelevant taxa, which can cause duplicate IDs, slower searches, and ambiguous results.

A customized BLASTn database solves these issues by including only relevant sequences, removing duplicates, and ensuring faster searches, and reproducible results.


<br />


## **blastdbbuilder**

`blastdbbuilder` is a lightweight, command-line toolkit that automates the complete **BLASTn database preparation workflow**. It streamlines all steps — from downloading user-specified genomes and organizing datasets, to building optimized and up-to-date BLASTn databases.

Designed for **researchers and clinicians**, it provides a **reproducible, regularly updated, and portable solution** for constructing BLAST databases **without manual setup**. 

The toolkit leverages:
  - **Pre-pulled Singularity containers**  
  - **Modular shell scripts**  

This enables:
  - **Easy deployment**  
  - **No dependency installation**  
  - A **smooth user experience** across different computational environments  
  - **Automatic cleanup of intermediate files**, keeping only the final BLAST database, which **drastically reduces disk space requirements**

Furthermore, `blastdbbuilder` retrieves genomes directly from **NCBI’s FTP servers**, ensuring that all downloaded sequences are as **current as the runtime**.


<br />

## **Features**

- Automated genome download for Archaea, Bacteria, Fungi, and Viruses
  
- Resume-able BLASTn DB creation — continue from interrupted runs
   
- Modular bash scripts for each task
    
- Optional use of pre-pulled Singularity containers for portability
    
- Lightweight installation (`pip install .`)
  
- Less disk space requirement 
 

<br />

## **Pre-requisite**

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

<br />

## Usage

  - There are three steps from downloading the genomes to building a BLASTn database
  
  - Open a terminal
  
  - Make a directory. Name it based on which group/s you are going to download. For example
  

    ```
    mkdir bacteria
    ```   

Or, maybe something like this if you are going to download archaea (a), bacteria (b), fungi (f), virus (v), and plants (p). This will help remember what are in the database files which will look like nt.001, nt.002, nt.003 and so on

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
    
  - When the run finished, you will clean up all the intermediate files and directories to reduce disk space usage
    
  - You will see only one directory named blastnDB
    
  - blastnDB will contain all the database files

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



### You have just created your customised BLASTn database. It is **fully portable**, can be moved to other users/computers and used without making any changes



