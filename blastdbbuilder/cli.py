#!/usr/bin/env python3
"""
blastdbbuilder CLI

A unified interface to automate:
1. Downloading genomes for Archaea, Bacteria, Fungi, and Viruses
2. Concatenating FASTA files
3. Building BLAST databases from concatenated genomes
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def run_script(script_name, *args):
    """Run a shell script from the scripts directory."""
    base_dir = Path(__file__).parent
    scripts_dir = os.environ.get("BLASTDBBUILDER_SCRIPTS", base_dir / "scripts")
    script_path = Path(scripts_dir) / script_name
    if not script_path.exists():
        sys.exit(f"❌ Script not found: {script_path}")
    print(f"🔹 Running {script_name} ...")
    try:
        subprocess.run(["bash", str(script_path), *args], check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(f"❌ Script {script_name} failed with exit code {e.returncode}")

def handle_download(args):
    """Download genomes based on selected groups."""
    print("🚀 Starting genome download workflow...")
    if args.archaea:
        print("📂 Downloading Archaea genomes...")
        run_script("archaea_ref_genomes_pipeline_bioinf_AP.sh")
    if args.bacteria:
        print("📂 Downloading Bacteria genomes...")
        run_script("bacteria_ref_genomes_pipeline_resume_bioinf_AP.sh")
    if args.fungi:
        print("📂 Downloading Fungi genomes...")
        run_script("fungi_ref_genomes_pipeline_bioinf_AP.sh")
    if args.virus:
        print("📂 Downloading Virus genomes...")
        run_script("virus_genomes_pipeline_bioinf_AP.sh")
    if not any([args.archaea, args.bacteria, args.fungi, args.virus]):
        sys.exit("⚠️ Specify at least one group with --archaea, --bacteria, --fungi, or --virus.")

def handle_concat():
    """Concatenate genome FASTA files."""
    print("🔧 Concatenating all genome FASTA files...")
    run_script("fasta-concat_20251014_AP.sh")

def handle_build():
    """Build BLAST database."""
    print("🧬 Building BLAST database...")
    run_script("makeblastdb_bioinf_AP_20251003_v5_seqkit_RESUME_Alias_AutoDetect_v3_NameLikeNCBI2.sh")

def handle_citation():
    """Print citation information."""
    citation_file = Path(__file__).parent.parent / "CITATION"
    if citation_file.exists():
        with open(citation_file, "r") as f:
            print(f.read())
    else:
        print("CITATION file not found. Please refer to the GitHub repository.")
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description="blastdbbuilder: Automated genome download, concatenation, and BLAST database builder"
    )

    parser.add_argument("--download", action="store_true", help="Download genomes for selected groups")
    parser.add_argument("--concat", action="store_true", help="Concatenate all genomes into one FASTA")
    parser.add_argument("--build", action="store_true", help="Build BLAST database from concatenated FASTA")
    parser.add_argument("--citation", action="store_true", help="Print citation information")

    # Download group flags
    parser.add_argument("--archaea", action="store_true", help="Include Archaea genomes")
    parser.add_argument("--bacteria", action="store_true", help="Include Bacteria genomes")
    parser.add_argument("--fungi", action="store_true", help="Include Fungi genomes")
    parser.add_argument("--virus", action="store_true", help="Include Virus genomes")

    args = parser.parse_args()

    if args.citation:
        handle_citation()
    elif args.download:
        handle_download(args)
    elif args.concat:
        handle_concat()
    elif args.build:
        handle_build()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
