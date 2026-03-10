
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

## **blastdbbuilder GUI**

`blastdbbuilder GUI` is a Linux graphical front‑end for the `blastdbbuilder` command‑line toolkit.

It enables users to:

- download public reference genomes
- concatenate genome FASTA files
- build customised BLASTn databases

using an interactive graphical interface.

The GUI internally executes the same backend commands as the original `blastdbbuilder` toolkit.

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

Install `blastdbbuilder-gui` directly from PyPI:

```
pip install blastdbbuilder-gui
```

Verify installation

Check if the installation was successful:

```
blastdbbuilder-gui
```

If the GUI window opens, then:

- the `installation` has been successful

- you can run `blastdbbuilder-gui` from any directory on your computer.


(Optional) Create a Desktop launcher (Linux)

Run once:


```
blastdbbuilder-gui-desktop
```

This creates a Desktop launcher (Linux). You can then double-click the Desktop icon to start the GUI.

<br />

---

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

## **How to use the GUI locally**

1. Launch the program using the desktop icon or:

```
blastdbbuilder-gui
```

2. Select the working directory through navigating into the directory and DOUBLE-CLICK the folder to select it, and then pressing OK

3. Choose genome groups:

- Archaea
- Bacteria
- Fungi
- Virus
- Plants

4. Select action:

- Download only
- Concat only
- Build only
- Run all

5. Enable **Run in background**.

6. Click **Run**.

Jobs continue running even if the GUI is closed.

---

## **How to use the GUI remotely**

The GUI is fully supported on remote Linux and HPC systems using X11 forwarding.

1. From your local computer, connect to the remote machine:

```
ssh -X user@remote_server
```

2. Then open a terminal and run the following command

```
blastdbbuilder-gui
```

This will open the blastdbbuilder GUI on your local screen. Then, run the job as you would do it locally. See **How to Use the GUI Locally**

---

## **Checking progress later**

1. Launch the GUI again by double-clicking on the Desktop icon (if you use it locally) or by running `blastdbbuilder-gui` in a terminal 
2. Click **Browse…**
3. Navigate to the **same working directory**
4. **DOUBLE-CLICK** that directory to select it
5. Click **Detect running job**

The GUI will reconnect and continue displaying the live log.

**This directory selection step is essential. The GUI cannot detect jobs without using the same directory.**

---

## **Stopping a job**

To stop a running job:

1. Select the same working directory
2. Click **Detect running job**
3. Click **Stop**

If the job does not stop (for example, a stalled container), click **Force Kill**.

---

## **Citation**

If you use this software in your work, please cite:

Prodhan, M. A. (2025). blastdbbuilder: Building a Customised BLASTn Database. https://doi.org/10.5281/zenodo.17394137

---

## **Support**

For issues, bug reports, or feature requests, please contact:

**Asad Prodhan**  
E-mail: asad.prodhan@dpird.wa.gov.au, prodhan82@gmail.com
