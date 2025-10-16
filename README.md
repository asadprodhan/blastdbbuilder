
<h1 align="center">blastdbbuilder: Building a Customised Blastn Database</h1>


<h3 align="center">M. Asaduzzaman Prodhan<sup>*</sup> </h3>


<div align="center"><b> DPIRD Diagnostics and Laboratory Services </b></div>


<div align="center"><b> Department of Primary Industries and Regional Development </b></div>


<div align="center"><b> 3 Baron-Hay Court, South Perth, WA 6151, Australia </b></div>


<div align="center"><b> *Correspondence: prodhan82@gmail.com </b></div>


<br />


<p align="center">
  <a href="https://github.com/asadprodhan/blastdbbuilder/tree/main?tab=GPL-3.0-1-ov-file#readme"><img src="https://img.shields.io/badge/License-GPL%203.0-yellow.svg" alt="License GPL 3.0" style="display: inline-block;"></a>
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
python3 -m pip install .
```

---

<br />



