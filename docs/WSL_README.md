
<h1 align="center">blastdbbuilder GUI: Graphical Interface for Building Customised BLASTn Databases</h1>

<h3 align="center">M. Asaduzzaman Prodhan<sup>*</sup> </h3>

<div align="center"><b> DPIRD Diagnostics and Laboratory Services </b></div>
<div align="center"><b> Department of Primary Industries and Regional Development </b></div>
<div align="center"><b> 31 Cedric St, Stirling WA 6021, Australia </b></div>
<div align="center"><b> *Correspondence: asad.prodhan@dpird.wa.gov.au; prodhan82@gmail.com </b></div>

<br />

<p align="center">
  <a href="https://github.com/asadprodhan/blastdbbuilder/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-GPL%203.0-yellow.svg" alt="License GPL 3.0"></a>
  <a href="https://orcid.org/0000-0002-1320-3486"><img src="https://img.shields.io/badge/ORCID-green?style=flat-square&logo=ORCID&logoColor=white" alt="ORCID"></a>
  <a href="https://doi.org/10.5281/zenodo.18973405"><img src="https://img.shields.io/badge/DOI-10.5281%2Fzenodo.18973405-blue?style=flat-square&logo=Zenodo&logoColor=white" alt="DOI: 10.5281/zenodo.18973405" style="display: inline-block;">
</p>

## **Content**

<img src="https://raw.githubusercontent.com/asadprodhan/blastdbbuilder/main/blastdbbuilder_logo.png"
     width="190"
     align="right">

- [Introduction](#introduction)
- [Features](#features)
- [Running blastdbbuilder GUI on Windows (WSL)](#running-blastdbbuilder-gui-on-windows-wsl)
- [Pre-requisite](#pre-requisite)
- [Installation](#installation)
- [GUI Controls](#gui-controls)
- [Access Windows Files from WSL](#access-windows-files-from-wsl)
- [Workflow 1. Reference Genomes](#workflow-1-reference-genomes)
- [Workflow 2. Local FASTA Database](#workflow-2-local-fasta-database)
- [Output Files](#output-files)
- [FAQ](#faq)
- [Entire Workflow Diagram](#entire-workflow-diagram)
- [Summary](#summary)
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

To simplify this process for Windows users, **blastdbbuilder GUI** can
run through **Windows Subsystem for Linux (WSL)** while providing the
same Linux-based blastdbbuilder backend.

Version 1.2.0 supports both construction from NCBI reference genomes and
direct construction from local FASTA collections.

---


## **Features**

-   Graphical selection of genome groups (Archaea, Bacteria, Fungi,
    Virus, Plants)

-   Build customised BLASTn databases directly from local FASTA files
    (`.fasta`, `.fa`, `.fna`, and `.fas`)

-   Separate **Reference Genomes** and **Local FASTA Database** tabs

-   Automatic handling of local FASTA collections --- use a single
    FASTA directly or concatenate multiple FASTA files before database
    construction

-   Graphical execution of genome download, FASTA concatenation, and
    BLASTn database construction

-   Background execution

-   Reconnect to running jobs

-   Live log monitoring

-   Safe termination and emergency kill options

-   Directory-based job management

---


## **Running blastdbbuilder GUI on Windows (WSL)**

`blastdbbuilder` can be run on Windows using **Windows Subsystem for
Linux (WSL)**.

WSL provides a Linux environment on Windows, allowing the
`blastdbbuilder` backend and GUI to use the same Linux-based workflow
used on standalone Linux systems.

Windows 11 with WSLg normally supports Linux graphical applications
directly. The GUI can therefore be launched from WSL with:

```bash
blastdbbuilder-gui
```

---


## **Pre-requisite**

**System requirements**

Before installing `blastdbbuilder-gui`, make sure the following are
available inside WSL:

**Python ≥ 3.9**

Check your Python version:

```bash
python3 --version
```

If required, install Python:

```bash
sudo apt install python3
```

**tkinter**

Check whether tkinter is available:

```bash
python3 -m tkinter
```

If a small window appears, tkinter is installed and graphical Linux
applications are working.

If tkinter is missing:

```bash
sudo apt install python3-tk
```

**unzip**

Check:

```bash
unzip -v
```

Install if missing:

```bash
sudo apt install unzip
```

**Container engine**

One of the following supported container engines is required:

-   Apptainer
-   SingularityCE ≥ 3.x

The program automatically detects which supported container engine is
available and uses it.

> Container-runtime installation and support under WSL can depend on
> the WSL distribution and configuration. Confirm that your selected
> Singularity/Apptainer installation works inside WSL before running
> large database builds.

---


## **Installation**

Install `blastdbbuilder-gui` from PyPI inside WSL:

```bash
pip install blastdbbuilder-gui
```

The GUI package installs the required `blastdbbuilder` core package as a
dependency.

To upgrade:

```bash
pip install --upgrade blastdbbuilder-gui
```

Verify the installation:

```bash
blastdbbuilder-gui
```

If the GUI opens, the installation has been successful.

If a user-level pip installation is not on your PATH, add:

```bash
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

The GUI can also be launched from Windows with:

```text
wsl.exe bash -lc "blastdbbuilder-gui"
```

---

<br />
<p align="center">
<img src="https://raw.githubusercontent.com/asadprodhan/blastdbbuilder/main/gui/GUI_Screenshot.png" width="100%">
</p>

<p><strong>Figure 1.</strong> blastdbbuilder graphical user interface (GUI) for building customised BLASTn databases from NCBI RefSeq genomes or local FASTA collections.</p>

---


## **GUI Controls**

The **Action** area provides two workflow tabs:

-   **Reference Genomes**
-   **Local FASTA Database**

For the Reference Genomes workflow:

**Browse...** Select the working directory.

**Detect running job** Reconnect to a running job associated with the
selected working directory.

**Run** Start the selected action.

**Stop** Gracefully stop the running job.

**Force Kill** Immediately terminate the job and related processes.

**Clear log view** Clear the GUI log window only.

**Exit** Close the GUI window.

The **Local FASTA Database** tab provides its own FASTA-directory
selection and workflow controls described below.

---


## **Access Windows Files from WSL**

Windows drives are normally mounted under `/mnt` inside WSL.

For example, the Windows `C:` drive is available at:

```text
/mnt/c
```

A Windows Downloads directory will typically be available at:

```text
/mnt/c/Users/YourWindowsUserName/Downloads
```

From WSL, you can navigate there with:

```bash
cd /mnt/c/Users/YourWindowsUserName/Downloads
```

Create a working directory if required:

```bash
mkdir -p db
cd db
```

Then launch the GUI:

```bash
blastdbbuilder-gui
```

When using the GUI directory chooser, navigate to `/mnt/c` to access
files stored on the Windows `C:` drive.

> For large databases, choose a location with sufficient free disk
> space.

---


## **Workflow 1. Reference Genomes**

Use the **Reference Genomes** tab when you want blastdbbuilder to
download selected NCBI genome collections and construct the database.

### **Step 1. Launch the GUI**

From WSL:

```bash
blastdbbuilder-gui
```

### **Step 2. Select the Working Directory**

Click **Browse...** and select the required working directory.

For a directory stored on Windows, navigate through `/mnt/c`.

### **Step 3. Select Genome Groups**

Choose one or more groups:

-   Archaea
-   Bacteria
-   Fungi
-   Virus
-   Plants

For large downloads, you may choose to process one genome group at a
time.

### **Step 4. Select an Action**

Available actions are:

-   Download only
-   Concat only
-   Build only
-   Run all

**Run all** performs the complete workflow:

```text
Download genomes
      ↓
Concatenate FASTA files
      ↓
Build BLASTn database
```

Enable **Run in background** when background execution is required, then
click **Run**.

---


## **Workflow 2. Local FASTA Database**

Use the **Local FASTA Database** tab to build a customised BLASTn
database directly from FASTA files already stored on your Windows or
WSL filesystem.

Supported extensions are:

-   `.fasta`
-   `.fa`
-   `.fna`
-   `.fas`

### **Step 1. Browse FASTA Directory**

Click **Browse FASTA Directory**.

To use FASTA files stored on Windows, navigate to a directory under:

```text
/mnt/c/Users/YourWindowsUserName/
```

Select the directory containing your FASTA files. The GUI displays the
selected path and detected FASTA file information.

### **Step 2. Concat only**

If multiple supported FASTA files are detected, **Concat only** can be
used to concatenate them before database construction.

If exactly one FASTA file is detected, concatenation is unnecessary and
**Concat only** is disabled.

The original FASTA files are preserved.

### **Step 3. Build only**

Click **Build only** to construct the BLASTn database from the selected
FASTA input.

The resulting database is written using the `nt` prefix:

```text
blastnDB/nt.*
```

### **Run all**

Click **Run all** to execute the complete local FASTA workflow.

For multiple FASTA files:

```text
Select FASTA directory
        ↓
Concatenate FASTA files
        ↓
Build BLASTn database
```

For a single FASTA file, the concatenation step is skipped and the file
is used directly for database construction.

---


## **Output Files**

After successful database construction, the final BLASTn database is
available under:

```text
blastnDB/nt.*
```

The exact database component files can vary with the BLAST+ database
format/version.

The database can be addressed with the prefix:

```text
blastnDB/nt
```

For example:

```bash
blastn -query query.fasta -db blastnDB/nt
```

---


## **FAQ**

### **1. How do I check WSL resources?**

Check RAM:

```bash
free -h
```

Check CPU cores:

```bash
nproc
```

Check detailed CPU information:

```bash
lscpu
```

Check disk space:

```bash
df -h
```

Check disk usage in the current directory:

```bash
du -sh *
```

### **2. Can blastdbbuilder use my laptop's resources?**

Yes. WSL uses resources provided by the Windows host.

The exact amount of CPU, RAM, disk, and swap available depends on the
computer and WSL configuration.

Check the resources actually available to your WSL environment using
the commands above rather than assuming a fixed percentage of the
laptop's hardware.

**Optional: configure WSL 2 resources**

A Windows `.wslconfig` file can be used to configure resource limits.
For example:

```text
[wsl2]
memory=12GB
processors=6
swap=4GB
```

After changing the configuration, shut down WSL from Windows:

```text
wsl --shutdown
```

Then restart your WSL distribution.

### **3. Can I create a Windows Desktop shortcut?**

Yes. Create a Windows shortcut whose target runs:

```text
wsl.exe bash -lc "blastdbbuilder-gui"
```

Name the shortcut, for example:

```text
blastdbbuilder
```

Double-clicking the shortcut will start the GUI through WSL, provided
WSL and the GUI environment are configured correctly.

### **4. Can I build directly from FASTA files stored on Windows?**

Yes. In the **Local FASTA Database** tab, browse to the Windows
directory through `/mnt/c/Users/...` and select the directory containing
your FASTA files.

The GUI can then use the selected FASTA collection to build the BLASTn
database.

---


## **Entire Workflow Diagram**

```text
+-------------------+
|   Windows Laptop  |
+-------------------+
          |
          v
+-------------------+
|        WSL        |
|   Ubuntu Linux    |
+-------------------+
          |
          v
+----------------------------+
|     blastdbbuilder GUI     |
+----------------------------+
          |
          v
+----------------------------+
|      Select workflow       |
+----------------------------+
      |                 |
      v                 v
+-------------+   +-------------------+
| NCBI        |   | Local FASTA       |
| genomes     |   | collection        |
+-------------+   +-------------------+
      |                 |
      v                 v
+-------------+   +-------------------+
| Download    |   | Use one FASTA or  |
| genomes     |   | concat multiple   |
+-------------+   +-------------------+
      |                 |
      v                 |
+-------------+         |
| Concatenate |         |
| FASTA       |         |
+-------------+         |
      |                 |
      +--------+--------+
               |
               v
+----------------------------+
|   Build BLASTn database    |
+----------------------------+
               |
               v
+----------------------------+
|       blastnDB/nt.*        |
+----------------------------+
```

---


## **Summary**

Using WSL, `blastdbbuilder` can provide Windows users with the same
Linux-based database-building workflow used by the core toolkit.

Version 1.2.0 provides two GUI workflows: construction from NCBI
reference genomes and construction directly from local FASTA files.

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
