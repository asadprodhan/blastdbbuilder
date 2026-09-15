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
  <a href="https://doi.org/10.5281/zenodo.18973405"><img src="https://img.shields.io/badge/DOI-10.5281%2Fzenodo.18973405-blue?style=flat-square&logo=Zenodo&logoColor=white" alt="DOI: 10.5281/zenodo.18973405" style="display: inline-block;"></a>
</p>


## **Content**

<img src="https://raw.githubusercontent.com/asadprodhan/blastdbbuilder/main/blastdbbuilder_logo.png"
     width="190"
     align="right">

- [Introduction](#introduction)
- [blastdbbuilder GUI](#blastdbbuilder-gui)
- [Features](#features)
- [Pre-requisite](#pre-requisite)
- [Installation](#installation)
- [Graphical User Interface](#graphical-user-interface)
- [GUI Controls](#gui-controls)
- [Workflow 1. Reference Genomes](#workflow-1-reference-genomes)
- [Workflow 2. Local FASTA Database](#workflow-2-local-fasta-database)
- [How to use the GUI remotely](#how-to-use-the-gui-remotely)
- [Checking progress later](#checking-progress-later)
- [Stopping a job](#stopping-a-job)
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

To simplify this process for end users, **blastdbbuilder GUI** provides
a graphical interface to the `blastdbbuilder` backend, allowing
reproducible database construction without requiring command-line
interaction.

Version 1.2.0 introduces a second database-building workflow, allowing
users to build a customised BLASTn database directly from their own
local FASTA files.

---


## **blastdbbuilder GUI**

`blastdbbuilder GUI` is a Linux graphical front-end for the
`blastdbbuilder` command-line toolkit.

The GUI provides two database-building workflows:

-   **Reference Genomes** --- download selected NCBI RefSeq genome
    collections, concatenate FASTA files, and build a customised BLASTn
    database

-   **Local FASTA Database** --- build a customised BLASTn database
    directly from local `.fasta`, `.fa`, `.fna`, or `.fas` files

The GUI internally executes the same reproducible backend as the
`blastdbbuilder` command-line toolkit.

---


## **Features**

-   Graphical selection of genome groups (Archaea, Bacteria, Fungi,
    Virus, Plants)

-   Build customised BLASTn databases directly from local FASTA files
    (`.fasta`, `.fa`, `.fna`, and `.fas`)

-   Automatic handling of local FASTA collections --- use a single
    FASTA file directly or concatenate multiple FASTA files before
    database construction

-   Separate **Reference Genomes** and **Local FASTA Database** tabs

-   Graphical execution of download, concatenation, and BLASTn database
    construction

-   Background execution

-   Reconnect to running jobs

-   Live log monitoring

-   Safe termination and emergency kill options

-   Directory-based job management

---


## **Pre-requisite**

**System requirements**

Before installing `blastdbbuilder-gui`, make sure the following are
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

**tkinter**

The GUI requires `tkinter`.

Check if it is available:

```bash
python3 -m tkinter
```

If a small window appears, tkinter is installed.

If tkinter is missing on Ubuntu:

```bash
sudo apt install python3-tk
```

**unzip**

Check if `unzip` is installed:

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

Install `blastdbbuilder-gui` directly from PyPI:

```bash
pip install blastdbbuilder-gui
```

The GUI package installs the required `blastdbbuilder` core package as a
dependency.

To upgrade to the latest release:

```bash
pip install --upgrade blastdbbuilder-gui
```

Verify the installation:

```bash
blastdbbuilder-gui
```

If the GUI window opens, the installation has been successful.

**Optional: Create a Desktop launcher (Linux)**

Run once:

```bash
blastdbbuilder-gui-desktop
```

You can then use the Desktop launcher to start the GUI.

---


## **Graphical User Interface**

<br />
<p align="center">
<img src="https://raw.githubusercontent.com/asadprodhan/blastdbbuilder/main/gui/GUI_Screenshot.png" width="100%">
</p>

<p><strong>Figure 1.</strong> blastdbbuilder graphical user interface (GUI) for building customised BLASTn databases from NCBI RefSeq genomes or local FASTA collections.</p>

The **Action** area contains two tabs:

-   **Reference Genomes**
-   **Local FASTA Database**

Select the workflow appropriate for the database you want to build.

---


## **GUI Controls**

**Browse...** Select the working directory for the Reference Genomes
workflow.

**Detect running job** Reconnect to a running job associated with the
selected working directory.

**Run** Start the selected action.

**Stop** Gracefully stop the running job.

**Force Kill** Immediately terminate the job and related processes.

**Clear log view** Clear the GUI log window only.

**Exit** Close the GUI window.

The **Local FASTA Database** tab additionally provides controls for
selecting the FASTA directory and running the local FASTA workflow.

---


## **Workflow 1. Reference Genomes**

Use the **Reference Genomes** tab when you want `blastdbbuilder` to
download genome collections and construct the database.

1. Launch the GUI:

```bash
blastdbbuilder-gui
```

2. Click **Browse...** and select the working directory.

> Choose a working directory with sufficient storage for the downloaded
> genomes and database files.

3. Choose one or more genome groups:

-   Archaea
-   Bacteria
-   Fungi
-   Virus
-   Plants

4. Select an action:

-   Download only
-   Concat only
-   Build only
-   Run all

5. Enable **Run in background** when background execution is required.

6. Click **Run**.

**Run all** executes the complete Reference Genomes workflow:
download → concatenate → build.

Jobs started in background mode can continue running after the GUI is
closed.

---


## **Workflow 2. Local FASTA Database**

Use the **Local FASTA Database** tab to build a customised BLASTn
database from your own FASTA collection.

Supported file extensions are:

-   `.fasta`
-   `.fa`
-   `.fna`
-   `.fas`

### **Step 1. Browse FASTA Directory**

Click **Browse FASTA Directory** and navigate to the directory
containing the FASTA files.

Select the required directory. The selected path and detected FASTA
file information are displayed in the GUI.

The directory chooser supports selecting the required folder and then
confirming it with **Select**.

### **Step 2. Concat only**

If multiple supported FASTA files are detected, **Concat only** can be
used to concatenate them before database construction.

If exactly one supported FASTA file is detected, concatenation is not
required and **Concat only** is disabled.

The original FASTA files are preserved.

### **Step 3. Build only**

Click **Build only** to construct the BLASTn database from the selected
local FASTA input.

The resulting database is written using the `nt` prefix under:

```text
blastnDB/nt.*
```

### **Run all**

Click **Run all** to execute the complete local FASTA workflow:

```text
1. Browse FASTA Directory
        ↓
2. Concatenate multiple FASTA files when required
        ↓
3. Build BLASTn database
```

For a directory containing a single FASTA file, the concatenation step
is skipped automatically and the file is used directly for database
construction.

---


## **How to use the GUI remotely**

The GUI can be used on remote Linux and HPC systems where graphical X11
forwarding is available.

From your local computer, connect to the remote machine using X11
forwarding:

```bash
ssh -X user@remote_server
```

Then run:

```bash
blastdbbuilder-gui
```

The GUI will open through the X11 session. You can then use either the
**Reference Genomes** or **Local FASTA Database** workflow as described
above.

---


## **Checking progress later**

For a background Reference Genomes job:

1. Launch `blastdbbuilder-gui` again.
2. Click **Browse...**.
3. Select the same working directory used to start the job.
4. Click **Detect running job**.

The GUI will reconnect to the job and continue displaying its live log.

**The same working directory is required for job detection because job
state is associated with that directory.**

---


## **Stopping a job**

To stop a running background job:

1. Select the same working directory.
2. Click **Detect running job**.
3. Click **Stop**.

If the job does not stop normally, for example because of a stalled
container process, click **Force Kill**.

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
