#!/usr/bin/env python3
"""
BlastDBBuilder CLI
"""

import argparse
import os
import glob
import shutil
import subprocess
from datetime import datetime

# -----------------------------
# Helper Functions
# -----------------------------
def write_summary(summary_log, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(summary_log, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

def run_cmd(cmd_list):
    try:
        result = subprocess.run(cmd_list, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {' '.join(cmd_list)}")
        return False

# -----------------------------
# Concatenate genomes
# -----------------------------
def concat_genomes(db_dir, summary_log):
    concat_dir = os.path.join(db_dir, "concat")
    os.makedirs(concat_dir, exist_ok=True)
    output_fasta = os.path.join(concat_dir, "combined_fasta.fasta")

    fasta_files = []
    for ext in ("*.fna", "*.fa", "*.fasta"):
        fasta_files.extend(glob.glob(os.path.join(db_dir, "**", ext), recursive=True))

    if not fasta_files:
        print("❌ No genome FASTA files found to concatenate")
        return None

    print(f"Concatenating {len(fasta_files)} genome files...")
    total_sequences = 0
    with open(output_fasta, "w") as out_f:
        for fasta in fasta_files:
            with open(fasta) as f:
                for line in f:
                    out_f.write(line)
                    if line.startswith(">"):
                        total_sequences += 1

    # Move concatenated file one level up from db/
    project_root = os.path.abspath(os.path.join(db_dir, ".."))
    final_fasta = os.path.join(project_root, "combined_fasta.fasta")
    shutil.move(output_fasta, final_fasta)

    # Clean up
    shutil.rmtree(concat_dir, ignore_errors=True)
    shutil.rmtree(db_dir, ignore_errors=True)

    write_summary(summary_log, f"✅ Concatenated {len(fasta_files)} files, {total_sequences} sequences into {final_fasta}")
    print(f"✅ Concatenation done. File moved to {final_fasta}")
    return final_fasta

# -----------------------------
# Build BLAST DB
# -----------------------------
def build_blast_db(fasta_file, summary_log, chunk_size="3G"):
    if not os.path.isfile(fasta_file):
        print(f"❌ FASTA file {fasta_file} not found for BLAST DB build")
        write_summary(summary_log, f"❌ FASTA {fasta_file} missing, BLAST DB build aborted")
        return

    project_root = os.path.dirname(fasta_file)
    db_dir = os.path.join(project_root, "blastnDB")
    os.makedirs(db_dir, exist_ok=True)

    print(f"Building BLAST database from {fasta_file}...")
    db_basename = "combined_db"
    db_prefix = os.path.join(db_dir, db_basename)
    blast_cmd = [
        "makeblastdb",
        "-in", fasta_file,
        "-dbtype", "nucl",
        "-out", db_prefix,
        "-parse_seqids",
        "-hash_index"
    ]

    success = run_cmd(blast_cmd)
    if success:
        write_summary(summary_log, f"✅ BLAST DB built: {db_prefix}")
        print(f"✅ BLAST DB successfully built at {db_prefix}")
    else:
        write_summary(summary_log, f"❌ BLAST DB build failed for {fasta_file}")
        print(f"❌ BLAST DB build failed for {fasta_file}")

# -----------------------------
# Download placeholder
# -----------------------------
def download_group(group_name, summary_log):
    print(f"📦 Downloading {group_name} genomes... (placeholder)")
    write_summary(summary_log, f"📦 Downloaded {group_name} genomes (placeholder)")

# -----------------------------
# Main CLI
# -----------------------------
def main():
    parser = argparse.ArgumentParser(description="BlastDBBuilder CLI")
    parser.add_argument("--archaea", action="store_true")
    parser.add_argument("--bacteria", action="store_true")
    parser.add_argument("--fungi", action="store_true")
    parser.add_argument("--virus", action="store_true")
    parser.add_argument("--plants", action="store_true")
    parser.add_argument("--concat", action="store_true", help="Concatenate downloaded genomes")
    parser.add_argument("--build", action="store_true", help="Build BLAST DB from concatenated genomes")
    args = parser.parse_args()

    project_root = os.path.abspath(os.getcwd())
    db_dir = os.path.join(project_root, "db")
    os.makedirs(db_dir, exist_ok=True)

    summary_log = os.path.join(project_root, "summary.log")

    # -----------------------------
    # Download
    # -----------------------------
    for group_flag, group_name in [
        (args.archaea, "archaea"),
        (args.bacteria, "bacteria"),
        (args.fungi, "fungi"),
        (args.virus, "virus"),
        (args.plants, "plants")
    ]:
        if group_flag:
            download_group(group_name, summary_log)

    # -----------------------------
    # Concatenate
    # -----------------------------
    combined_fasta = None
    if args.concat:
        combined_fasta = concat_genomes(db_dir, summary_log)

    # -----------------------------
    # Build BLAST DB
    # -----------------------------
    if args.build:
        if not combined_fasta:
            combined_fasta = os.path.join(project_root, "combined_fasta.fasta")
        build_blast_db(combined_fasta, summary_log)

if __name__ == "__main__":
    main()
