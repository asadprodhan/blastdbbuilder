blastdbbuilder GUI (Linux) — Packaged Installer (template)

What you do:
1) Copy your BLAST container image into:
   blastdbbuilder-gui-linux/app/containers/

2) Take the folder to Linux, then:
   chmod +x *.sh app/run_gui.sh
   ./install.sh

What users do after install:
- A Desktop icon named 'blastdbbuilder' appears.
- Double-click it to open the GUI.
- For long downloads: run in background, close GUI, reopen later and click 'Detect running job'.

Requirements:
- python3 with tkinter
- apptainer or singularity on PATH
- blastdbbuilder CLI on PATH
