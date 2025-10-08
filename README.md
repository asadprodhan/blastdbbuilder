# Building a Custom BLAST Nucleotide Database: Troubleshooting Guide

This repository demonstrates how to build a BLAST nucleotide database from very large FASTA files using **NCBI BLAST+** inside a **Singularity container**. It also covers common errors and best practices when creating custom databases.

---

## Table of Contents

- [Introduction](#introduction)  
- [Prerequisites](#prerequisites)  
- [Workflow](#workflow)  
- [Common Errors & Fixes](#common-errors--fixes)  
- [Best Practices](#best-practices)  
- [References](#references)  

---

## Introduction

Custom BLAST databases are required for genomics or metagenomics projects. Large FASTA files and complex headers can trigger subtle errors, including **duplicate internal IDs**.

This guide focuses on **duplicate ID errors**, file size limits, and best practices for handling large nucleotide databases.

---

## Prerequisites

- Linux machine with sufficient memory (≥128 GB recommended for very large FASTA files).  
- **Singularity** installed (or Apptainer).  
- **NCBI BLAST+ 2.16+** container image (`ncbi-blast_2.16.0.sif`).  
- Input FASTA file(s) with **unique headers**, e.g., for genomes with multiple contigs:

> file1_seq1_NZ_JRKI01000001.1 Streptomyces
ATGCGT...

> file1_seq2_NZ_JRKI01000002.1 Streptomyces
CGTAGC...


---

## Workflow

### **1. Verify unique sequence headers**

```bash
awk '/^>/{print $1}' combined_fasta.fna | sed 's/^>//' | sort | uniq -d
```

**Explanation of each step:**

- awk '/^>/{print $1}' combined_fasta.fna
  Scans each line of combined_fasta.fna. If the line starts with > (FASTA header), it prints only the first word of the header (the sequence ID).

- sed 's/^>//'
  Removes the leading > from each printed ID.

- sort
  Sorts all the IDs alphabetically.

- uniq -d
  Prints only duplicate lines (IDs that appear more than once).

**Interpretation:**

- If all IDs are unique, the command produces no output.

- If there are duplicates, the duplicated IDs will be listed.

  Example headers:

  >file1_seq1_NZ_JRKI01000001.1
  >file1_seq2_NZ_JRKI01000002.1
  >file1_seq3_NZ_JRKI01000003.1


If your headers follow this pattern and are unique, the command will produce no output, confirming uniqueness.

2. **Split large FASTA files safely**

Each chunk must start with a header (>). Example: 30 GB chunks.

3. **Build BLAST database for each chunk**

singularity exec ncbi-blast_2.16.0.sif makeblastdb \
    -in chunk_aa.fna \
    -dbtype nucl \
    -blastdb_version 5 \
    -max_file_sz 3000000000B \
    -out nt_chunk_aa \
    -title "chunk_aa" \
    -hash_index \
    -logfile nt_chunk_aa.log

⚠️ The key fix for Duplicate seq_ids are found: GNL|BL_ORD_ID|#### is to set -max_file_sz = 3000000000B. BLAST will split the database internally to avoid duplicate internal IDs.

4. **Combine chunk databases using an alias file (.pal)**
   
The alias allows blastn to search across all chunks transparently.

TITLE Combined_nt_database
DBLIST nt_chunk_aa nt_chunk_ab nt_chunk_ac nt_chunk_ad


5. **Run BLAST queries against the alias database**

```
singularity exec ncbi-blast_2.16.0.sif \
    blastn -db blastnDB/nt -query your_query.fna -out results.txt
```

## Common Errors & Fixes

### 1. `Duplicate seq_ids are found: GNL|BL_ORD_ID|####`

- **Cause:** Internal BLAST IDs conflict for large databases.  
- **Fix:** Use `-max_file_sz = 3000000000B` to let BLAST split the database internally and avoid collisions.

### 2. `Input doesn't start with a defline or comment`

- **Cause:** A chunk file does not begin with `>` due to naïve splitting.  
- **Fix:** Ensure each chunk starts with a header line. The provided script handles safe splitting.

### 3. `blastdbcmd: executable file not found`

- **Cause:** Trying to run `blastdbcmd` outside the container or without the correct path.  
- **Fix:** Always run BLAST commands inside the container:

```bash
singularity exec ncbi-blast_2.16.0.sif blastdbcmd -info -db nt_chunk_aa
```

## Best Practices

- Always verify headers before building the database.  
- Split large FASTA files safely; do not cut sequences mid-way.  
- Use chunk databases with an alias to handle files exceeding ~3 GB.  
- Keep log files for each chunk to trace errors.  
- For genomes with multiple contigs, include unique file/sequence identifiers.  

## References

- [NCBI BLAST makeblastdb documentation](https://blast.ncbi.nlm.nih.gov/Blast.cgi)  
- Camacho et al., *Building a BLAST database with your (local) sequences*, Bookshelf NBK569841  
- [NCBI C++ Toolkit: ID Parser rules](https://ncbi.github.io/cxx-toolkit/pages/ch_demo#ch_demo.T5)


