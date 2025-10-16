#!/usr/bin/env python3
"""
blastdbbuilder CLI

Automates:
1. Downloading genomes for Archaea, Bacteria, Fungi, Viruses
2. Concatenating FASTA files
3. Building BLAST databases
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
import shutil

def run_script(script_name, *args):
    """Run a shell script from the BLASTDBBUILDER_SCRIPTS directory."""
    scripts_dir = os.environ.get("BLASTDBBUILDER_SCRIPTS")
    if not scripts_dir:
        sys.exit("❌ Error: BLASTDBBUILDER_SCRIPTS environment variable not set.")

    script_path = Path(scripts_dir) / script_name
    if not script_path.exists():
        sys.exit(f"❌ Script not found: {script_path}")

    print(f"🔹 Running {script_name} ...")
    try:
        subprocess.run(["bash", str(script_path), *args], check=True)
    except subprocess.CalledProcessError as e:
        sys.exit(f"❌ Script {script_name} failed with exit code {e.returncode}")

def handle_download(args):
    """Download genomes into db/<group>/ directories."""
    base_dir = Path.cwd() / "db"
    base_dir.mkdir(exist_ok=True)
    groups = {
        "archaea": "archaea_ref_genomes_pipeline_bioinf_AP.sh",
        "bacteria": "bacteria_ref_genomes_pipeline_resume_bioinf_AP.sh",
        "fungi": "fungi_ref_genomes_pipeline_bioinf_AP.sh",
        "virus": "virus_genomes_pipeline_bioinf_AP.sh",
    }

    selected_groups = []
    if args.archaea: selected_groups.append("archaea")
    if args.bacteria: selected_groups.append("bacteria")
    if args.fungi: selected_groups.append("fungi")
    if args.virus: selected_groups.append("virus")

    if not selected_groups:
        sys.exit("⚠️ Please specify at least one group with --archaea, --bacteria, --fungi, or --virus.")

    for group in selected_groups:
        group_dir = base_dir / group
        group_dir.mkdir(exist_ok=True)
        print(f"📂 Downloading {group} genomes into {group_dir} ...")
        run_script(groups[group], str(group_dir))

def handle_concat():
    """Concatenate all genomes from db/* into concat/."""
    db_dir = Path.cwd() / "db"
    concat_dir = Path.cwd() / "concat"
    concat_dir.mkdir(exist_ok=True)

    if not db_dir.exists():
        sys.exit("❌ db/ directory not found. Please run --download first.")

    fasta_extensions = ("*.fasta", "*.fna", "*.fa")
    count = 0
    for group_dir in db_dir.iterdir():
        if group_dir.is_dir():
            for ext in fasta_extensions:
                for fasta_file in group_dir.glob(ext):
                    target_file = concat_dir / fasta_file.name
                    shutil.move(str(fasta_file), str(target_file))
                    count += 1
    print(f"✅ Moved {count} genome FASTA files to {concat_dir}")

def handle_build():
    """Build BLAST DB from concat/."""
    concat_dir = Path.cwd() / "concat"
    if not concat_dir.exists():
        sys.exit("❌ concat/ directory not found. Please run --concat first.")
    print("🧬 Building BLAST database from concat/ ...")
    run_script("makeblastdb_bioinf_AP_20251003_v5_seqkit_RESUME_Alias_AutoDetect_v3_NameLikeNCBI2.sh")

def main():
    parser = argparse.ArgumentParser(
        description="blastdbbuilder: Automated genome download, concatenation, and BLAST database builder"
    )

    parser.add_argument("--download", action="store_true", help="Download genomes for selected groups")
    parser.add_argument("--concat", action="store_true", help="Concatenate all genomes into one FASTA")
    parser.add_argument("--build", action="store_true", help="Build BLAST database from concatenated FASTA")
    parser.add_argument("--citation", action="store_true", help="Print citation information")

    parser.add_argument("--archaea", action="store_true", help="Include Archaea genomes")
    parser.add_argument("--bacteria", action="store_true", help="Include Bacteria genomes")
    parser.add_argument("--fungi", action="store_true", help="Include Fungi genomes")
    parser.add_argument("--virus", action="store_true", help="Include Virus genomes")

    args = parser.parse_args()

    if args.citation:
        print("Asad Prodhan, blastdbbuilder, 2025. DOI: XXXX")
        return

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
