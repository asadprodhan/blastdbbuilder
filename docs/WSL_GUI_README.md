
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
  <a href="https://doi.org/10.5281/zenodo.17394137"><img src="https://img.shields.io/badge/DOI-10.5281%2Fzenodo.17394137-blue?style=flat-square&logo=Zenodo&logoColor=white" alt="DOI"></a>
</p>

---

## **Content**

- [Introduction](#introduction)
- [blastdbbuilder GUI](#blastdbbuilder-gui)
- [Features](#features)
- [Pre-requisite](#pre-requisite)
- [Installation](#installation)
- [Introduction of the Buttons and their meaning](#introduction-of-the-buttons-and-their-meaning)
- [How to use the GUI locally](#how-to-use-the-gui-locally)
- [How to use the GUI remotely](#how-to-use-the-gui-remotely)
- [Checking progress later](#checking-progress-later)
- [Stopping a job](#stopping-a-job)
- [Citation](#citation)
- [Support](#support)

---


## **Introduction**

A BLASTn database provides the essential reference framework for comparing query sequences, forming the backbone of any sequence-based analysis. Accurate results—whether in diagnostics, biosecurity surveillance, microbial studies, evolutionary research, environmental surveys, or functional genomics—depend on a high-quality, well-curated database.

Public databases are comprehensive but rapidly expanding, often containing redundant, low-quality or irrelevant entries. This leads to slower searches and reduced search resolution.

In contrast, a custom database is like a well‑organised library where every book is precisely indexed—smaller in volume, faster to search, and more focused in results.

To simplify this process for end users, **blastdbbuilder GUI** provides a graphical interface to the proven `blastdbbuilder` backend, allowing fully reproducible database construction without requiring command‑line interaction.

---

## **Features**

- Graphical selection of genome groups (Archaea, Bacteria, Fungi, Virus, Plants)
- Graphical execution of genome download, FASTA concatenation and BLAST database building
- Background execution (safe to close the GUI)
- Reconnect to running jobs
- Live log monitoring
- Safe termination and emergency kill options
- Directory‑based job management

---


## **Running blastdbbuilder GUI on Windows (WSL)**

`blastdbbuilder` can be run on Windows laptops using **Windows Subsystem for Linux (WSL)**.
This allows you to use the same Linux-based workflow used on HPC systems or standalone Linux station.


## **Pre-requisite**

**System requirements**

Before installing `blastdbbuilder`, make sure the following are available on your system:

**Python ≥ 3.9**

Check your Python version:

```
python3 --version
```

If Python is older than 3.9, install a newer Python using your system package manager.

Example (Ubuntu):

```
sudo apt install python3
```

This installs the latest Python version supported by your operating system.

You do not need to remove the existing Python installation, because Ubuntu uses Python internally for many system tools.


**tkinter**

The GUI requires the `tkinter` library for the graphical interface.

To check if tkinter is available:


```
python3 -m tkinter
```

If a small window appears, tkinter is installed.


If tkinter is missing (Ubuntu):


```
sudo apt install python3-tk
```


**unzip**

The program requires the unzip utility to extract downloaded genome archives.

Check if `unzip` is installed:

```
unzip -v
```

If the command is not found, install it:

```
sudo apt install unzip
```

**wget**

Check:

```
wget --version
```

Install if missing:

```
sudo apt install wget
```

**Container engine**

One of the following container engines must be installed:

- Apptainer

- SingularityCE ≥ 3.x

Example installation on Ubuntu / Debian:

```
sudo apt install singularity-container
```

The program automatically detects which container engine is available on your system and uses it.

On HPC systems (for example ARDC Nectar), Singularity or Apptainer is typically already installed.


---

## **Installation**

Install `blastdbbuilder-gui` directly from PyPI in your WSL:

```
pip install blastdbbuilder-gui
```

Verify installation by launching the GUI:

```
blastdbbuilder-gui
```

If the GUI window opens, then:

- the `installation` has been successful

- you can run `blastdbbuilder-gui` from any directory on your computer.


Add blastdbbuilder to your PATH by running the following commands:

```
echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
source ~/.bashrc
```

This ensures commands installed by pip can be run from any directory.


(Optional) Create a Desktop launcher (Linux)

WSL does not run a full Linux desktop environment, so the Desktop icon may not be visible in the same way as on a native Linux system.
The GUI can always be launched using:

```
wsl.exe -e blastdbbuilder-gui
```


<br /> <p align="center"> <img src="https://raw.githubusercontent.com/asadprodhan/blastdbbuilder/main/GUI/GUI_Screenshot.png" width="100%" > </p>

<p><strong>Figure 1.</strong> blastdbbuilder graphical user interface (GUI) automating construction of custom BLASTn reference databases from NCBI RefSeq genomes.</p>

---


## **Introduction of the Buttons and their meaning**

**Browse...** Select the working directory.

**Detect running job** Reconnect to a running job in the selected directory.

**Run** Starts the selected action.

**Stop** Gracefully stops the running job.

**Force Kill** Immediately terminates the job and all related processes.

**Clear log view** Clears the GUI log window only.

**Exit** Closes the GUI window.

---

## **Access Windows files from WSL**

Windows drives are available under `/mnt`.

Examples:

| Windows path | WSL path |
|--------------|----------|
| C:\ | /mnt/c |
| D:\ | /mnt/d |

Example:

```
C:\Users\username\Documents
```

becomes

```
/mnt/c/Users/username/Documents
```

When using the GUI **Browse** button, navigate to `/mnt` to access your Windows files.

---

## **Build a BLAST database on your laptop**

### Step 1 — Create a working directory

```
mkdir ~/blastdbbuilder_run
cd ~/blastdbbuilder_run
```

### Step 2 — Launch the GUI

```
wsl.exe -e blastdbbuilder-gui
```

### Step 3 — Select database groups

Choose the genomes you want to download:

- Archaea
- Bacteria
- Fungi
- Virus
- Plants

A good practice will be downloading one group at a time. Check the "Show failed genomes" tab and run "Try again (failed). Go back and forth between these two tabs until there is no genome in the "Show failed genomes" tab.

Then move on the next group.


### Step 4 — Run Concat

Click the "Concat" button.


### Step 5 — Run Build

Click the "Build" button.



The GUI will:

1. Download reference genomes from NCBI
2. Concatenate FASTA sequences
3. Build a BLAST nucleotide database

---

## **Output files**

After completion you will see:

```
blastnDB/
metadata/
summary.log
```

Example BLAST database files:

```
blastnDB/nt.nsq
blastnDB/nt.nin
blastnDB/nt.nhr
```

These can be used with:

```
blastn
megablast
local BLAST searches
```

---


## **FAQ**


## **1. How to check WSL resources (RAM, CPU, disk)**

### Check RAM

```
free -h
```

### Check CPU cores

```
nproc
```

### Detailed CPU information

```
lscpu
```

### Check disk space

```
df -h
```

### Check disk usage in the working directory

```
du -sh *
```

---

## **2. Can the laptop’s resources be used?**

Yes. WSL can use your laptop’s CPU, RAM, and disk resources.

Typical laptop example:

| Laptop Hardware | Available to WSL |
|-----------------|------------------|
| 16 GB RAM | ~12–14 GB usable |
| 8 CPU cores | All cores usable |
| 1 TB disk | Full disk accessible |

This means `blastdbbuilder` can build BLAST databases locally on your laptop.

### Optional: limit WSL resources

Create a configuration file:

```
C:\Users\USERNAME\.wslconfig
```

Example:

```
[wsl2]
memory=12GB
processors=6
swap=4GB
```

Restart WSL:

```
wsl --shutdown
```

---

## **3. Can the blastdbbuilder icon stay on the laptop screen?**

Yes. The best way is to create a **Windows desktop shortcut**.

Create a Windows shortcut that runs:

```
wsl.exe -e blastdbbuilder-gui
```

Steps:

1. Right‑click on the Windows Desktop
2. Select **New → Shortcut**
3. Enter:

```
wsl.exe bash -lc "blastdbbuilder-gui"
```
4. Name the shortcut:

```
blastdbbuilder
```

Now double‑clicking the icon launches the GUI.

---

## **Entire Workflow Diagram**


```
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
|  Download genomes (NCBI)   |
+----------------------------+
          |
          v
+----------------------------+
|  Concatenate FASTA files   |
+----------------------------+
          |
          v
+----------------------------+
|   Build BLAST Database     |
+----------------------------+
          |
          v
+----------------------------+
|        blastnDB/           |
|   nt.nsq nt.nin nt.nhr     |
+----------------------------+
```

---

## **Summary**

Using WSL, `blastdbbuilder` can run on a Windows laptop with the same workflow used on Linux servers and HPC systems. You can now build BLAST reference databases locally on your laptop.


## **Citation**

If you use this software in your work, please cite:

Prodhan, M. A. (2025). blastdbbuilder: Building a Customised BLASTn Database. https://doi.org/10.5281/zenodo.17394137

---

## **Support**

For issues, bug reports, or feature requests, please contact:

**Asad Prodhan**  
E-mail: asad.prodhan@dpird.wa.gov.au, prodhan82@gmail.com
