<h1 align="center">blastdbbuilder GUI: Building a Customised BLASTn Database</h1>

<h3 align="center">M. Asaduzzaman Prodhan<sup>*</sup> </h3>

<div align="center"><b> DPIRD Diagnostics and Laboratory Services </b></div>

<div align="center"><b> Department of Primary Industries and Regional Development </b></div>

<div align="center"><b> 31 Cedric St, Stirling WA 6021, Australia </b></div>

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
- [blastdbbuilder GUI](#blastdbbuilder-gui)
- [Features](#features)
- [Pre-requisite](#pre-requisite)
- [Installation](#installation)
- [Using the GUI](#using-the-gui)
  - [Working directory](#working-directory-very-important)
  - [Selecting a directory](#selecting-a-directory-important-note)
  - [Genome group selection](#genome-group-selection)
  - [Action selection](#action-selection)
  - [Buttons and their meaning](#buttons-and-their-meaning)
  - [Running a job](#running-a-job)
  - [Checking progress later](#checking-progress-later)
  - [Stopping a job](#stopping-a-job)
- [Citation](#citation)
- [Support](#support)
---

## **Introduction**

A BLASTn database provides the essential reference framework for comparing query sequences, forming the backbone of any sequence-based analysis. Accurate results—whether in diagnostics, biosecurity surveillance, microbial studies, evolutionary research, environmental surveys, or functional genomics—depend on a high-quality, well-curated database; without it, even the most sophisticated tools can yield ambiguous outcomes.

Public databases are comprehensive but rapidly expanding, often containing redundant, low-quality or irrelevant entries. This leads to slower searches and reduced search resolution.

In contrast, a custom database is like a well-organised library where every book is precisely indexed—smaller in volume, faster to search, and more focused in results.

To simplify this process for end users, **blastdbbuilder GUI** provides a graphical interface to the proven `blastdbbuilder` backend, allowing fully reproducible database construction without requiring command-line interaction.

---

## **blastdbbuilder GUI**

`blastdbbuilder GUI` is a Linux graphical front-end for the `blastdbbuilder` command-line toolkit.

It enables users to:

- download public reference genomes
- concatenate genome FASTA files
- build customised BLASTn databases

using an interactive graphical interface.

The GUI is specifically designed for:

- long-running downloads (many hours to days)
- remote Linux and HPC systems
- safe background execution
- reconnecting to running jobs after closing the interface

The GUI internally executes the same backend commands as the original `blastdbbuilder` toolkit.

---

## **Features**

- Graphical selection of genome groups (Archaea, Bacteria, Fungi, Virus, Plants)
- Graphical execution of:
  - genome download
  - FASTA concatenation
  - BLASTn database construction
- Background execution (safe to close the GUI)
- Reconnect to running jobs at any time
- Live log monitoring
- Safe termination and emergency kill options
- Directory-based job management (multiple jobs can run simultaneously in different folders)

---

## **Pre-requisite**

- The GUI package is fully self-contained and ships all required containers.
- You only need: i) Linux computer and ii) Singularity installed on the system
- No manual installation of BLAST, datasets, or auxiliary tools is required

---

## **Installation**

1. [Download the Linux GUI installer](https://github.com/asadprodhan/blastdbbuilder/releases)
  
2. Extract the downloaded file

```
unzip blastdbbuilder-gui-linux.zip
```
  
3. Navigate the packae directory

```
cd blastdbbuilder_package_gui
```
  
4. Install

```
./install.sh
```
  
Or, right-click on `install.sh` and run as program


After installation, a desktop icon named blastdbbuilder will be created. 

---

<br /> <p align="center"> <img src="https://github.com/asadprodhan/blastdbbuilderGUI/blob/main/blastdbbuilderGUI_v3.png" width="100%" > </p> <p> <strong>Figure 1. blastdbbuilder graphical user interface (GUI).</strong> 
The main window of blastdbbuilder (GUI) showing the end-to-end workflow controller for building custom BLAST databases. The interface allows users to select a **working directory** (top), choose genome groups to **download** (Archaea, Bacteria, Fungi, Virus and Plants), and select the **execution** step (Download only, Concat only, Build only, or Run all steps sequentially). A command preview panel displays the exact command that will be executed. The right-hand panel streams the **live log** output from running jobs. Users can run jobs in **background mode** (safe to close the GUI) and control execution using the **Run**, **Stop**, **Force Kill**, **Clear log view**, and **Exit** buttons. The **status bar** at the bottom reports whether a running job is detected in the selected working directory. </p> <br />

---

## **Introduction of the Buttons and their meaning**

**Browse...** Select the working directory.

**Detect running job** Reconnects the GUI to an already running job in the selected directory and attaches to its log.

**Run** Starts the selected action(s).

**Stop** Sends a graceful termination request to the running job in the selected directory.

**Force Kill** Immediately kills the running job and all related processes. Use only if the job does not stop using *Stop*.

**Clear log view** Clears the log display inside the GUI window only. The log file on disk is not deleted.

**Exit** Closes the GUI window only. If the job is running in background mode, it continues running.

---

## **How to use the GUI locally**

1. Launch the program by double-clicking the desktop icon.
2 Select the working directory through navigating into the directory and DOUBLE-CLICK the folder** to select it, and then pressing OK
3. Select one or more groups:
    - Archaea
    - Bacteria
    - Fungi
    - Virus
    - Plants
4. Select action (usually *Run all*)
    - Download only (Step 1)
    - Concat only (Step 2)
    - Build only (Step 3)
    - Run all (1 → 2 → 3)
5. Ensure *Run in background* is enabled (recommended)
6. Click **Run**

**The job will start and logs will appear in the right-hand panel. You can safely close the GUI after starting a job and check progress later**
 
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
