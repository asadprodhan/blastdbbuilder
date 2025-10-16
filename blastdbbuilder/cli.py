#!/usr/bin/env python3
"""
blastdbbuilder CLI

Triggers modular shell scripts for:
1. Downloading genomes
2. Concatenating FASTA files
3. Building BLAST databases

Container pulls are handled inside the scripts at runtime.
"""

import sys
import argparse
import subprocess
from pathlib import Path

def run_script(script_name, *args):
    """Run a shell script from the scripts directory."""
    scripts_dir = Path(__file__).parent / "scripts"
    script_path = scripts_dir / script_name
    if not script_path.exists():
        sys.exit(f"❌ Script not found: {script_path}")
    print(f"🔹 Running {script_name} ...")
    try:
        subprocess.run(["bash", str(script_path), *args], check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(f"❌ Script {script_name} failed with exit code {e.returncode}")

def handle_download(args):
    """Trigger genome download script(s)."""
    if args.archaea: run_script("archaea_ref_genomes_pipeline_bioinf_AP.sh")
    if args.bacteria: run_script("bacteria_ref_genomes_pipeline_resume_bioinf_AP.sh")
    if args.fungi: run_script("fungi_ref_genomes_pipeline_bioinf_AP.sh")
    if args.virus: run_script("virus_genomes_pipeline_bioinf_AP.sh")
    if not any([args.archaea, args.bacteria, args.fungi, args.virus]):
        sys.exit("⚠️ Please specify at least one group with --archaea, --bacteria, --fungi, or --virus.")

def handle_concat():
    """Trigger concatenation script."""
    run_script("fasta-concat_20251014_AP.sh")

def handle_build():
    """Trigger BLAST database build script."""
    run_script("makeblastdb_bioinf_AP_20251003_v5_seqkit_RESUME_Alias_AutoDetect_v3_NameLikeNCBI2.sh")

def main():
    parser = argparse.ArgumentParser(description="blastdbbuilder: trigger modular scripts for BLAST DB workflow")
    parser.add_argument("--download", action="store_true", help="Download genomes")
    parser.add_argument("--concat", action="store_true", help="Concatenate genome FASTA files")
    parser.add_argument("--build", action="store_true", help="Build BLAST database")
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
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
