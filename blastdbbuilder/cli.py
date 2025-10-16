#!/usr/bin/env python3
"""
blastdbbuilder CLI

A lightweight command-line toolkit to automate:
1. Downloading genomes for Archaea, Bacteria, Fungi, and Viruses
2. Concatenating FASTA files
3. Building BLAST databases from concatenated genomes
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
import shutil


def run_script(script_name, *args):
    """Run a shell script from the scripts directory inside the package."""
    current_dir = Path(__file__).parent
    scripts_dir = current_dir / "scripts"
    script_path = scripts_dir / script_name

    if not script_path.exists():
        sys.exit(f"❌ Script not found: {script_path}")

    print(f"🔹 Running {script_name} ...")
    try:
        subprocess.run(["bash", str(script_path), *args], check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(f"❌ Script {script_name} failed with exit code {e.returncode}")


def handle_download(args):
    """Download genomes for the selected groups."""
    cwd = Path.cwd()
    db_dir = cwd / "db"
    db_dir.mkdir(exist_ok=True)

    if args.archaea:
        target_dir = db_dir / "archaea"
        target_dir.mkdir(exist_ok=True)
        print(f"📂 Downloading Archaea genomes into {target_dir} ...")
        run_script("archaea_ref_genomes_pipeline_bioinf_AP.sh", str(target_dir))

    if args.bacteria:
        target_dir = db_dir / "bacteria"
        target_dir.mkdir(exist_ok=True)
        print(f"📂 Downloading Bacteria genomes into {target_dir} ...")
        run_script("bacteria_ref_genomes_pipeline_resume_bioinf_AP.sh", str(target_dir))

    if args.fungi:
        target_dir = db_dir / "fungi"
        target_dir.mkdir(exist_ok=True)
        print(f"📂 Downloading Fungi genomes into {target_dir} ...")
        run_script("fungi_ref_genomes_pipeline_bioinf_AP.sh", str(target_dir))

    if args.virus:
        target_dir = db_dir / "virus"
        target_dir.mkdir(exist_ok=True)
        print(f"📂 Downloading Virus genomes into {target_dir} ...")
        run_script("virus_genomes_pipeline_bioinf_AP.sh", str(target_dir))

    if not any([args.archaea, args.bacteria, args.fungi, args.virus]):
        sys.exit("⚠️ Please specify at least one group with --archaea, --bacteria, --fungi, or --virus.")


def handle_concat():
    """Concatenate all downloaded genomes into concat/ directory."""
    cwd = Path.cwd()
    db_dir = cwd / "db"
    concat_dir = cwd / "concat"
    concat_dir.mkdir(exist_ok=True)

    groups = ["archaea", "bacteria", "fungi", "virus"]
    for group in groups:
        group_dir = db_dir / group
        if group_dir.exists() and any(group_dir.iterdir()):
            for fasta_file in group_dir.glob("*.[fF][aA]*"):
                shutil.copy(fasta_file, concat_dir / fasta_file.name)
    print(f"🔧 All genomes concatenated into {concat_dir}")


def handle_build():
    """Trigger the BLAST database build script."""
    print("🧬 Building BLAST database...")
    run_script("makeblastdb_bioinf_AP_20251003_v5_seqkit_RESUME_Alias_AutoDetect_v3_NameLikeNCBI2.sh")


def handle_citation():
    """Print citation information."""
    print("""
blastdbbuilder: Automated BLASTn database builder
Asad Prodhan, 2025
GitHub: https://github.com/AsadProdhan/blastdbbuilder
Zenodo DOI: 10.5281/zenodo.YOUR_DOI
    """)


def main():
    parser = argparse.ArgumentParser(
        description="blastdbbuilder: Automated genome download, concatenation, and BLAST database builder"
    )

    parser.add_argument("--download", action="store_true", help="Download genomes for selected groups")
    parser.add_argument("--concat", action="store_true", help="Concatenate all genomes into concat/")
    parser.add_argument("--build", action="store_true", help="Build BLAST database from concatenated FASTA")
    parser.add_argument("--citation", action="store_true", help="Print citation information")

    parser.add_argument("--archaea", action="store_true", help="Include Archaea genomes")
    parser.add_argument("--bacteria", action="store_true", help="Include Bacteria genomes")
    parser.add_argument("--fungi", action="store_true", help="Include Fungi genomes")
    parser.add_argument("--virus", action="store_true", help="Include Virus genomes")

    args = parser.parse_args()

    if args.download:
        handle_download(args)
    elif args.concat:
        handle_concat()
    elif args.build:
        handle_build()
    elif args.citation:
        handle_citation()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
