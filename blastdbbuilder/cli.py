#!/usr/bin/env python3
"""
BlastDBBuilder CLI
Author: Asad Prodhan
Date: 2025-10-17
"""

import argparse
import subprocess
import sys
import os
from datetime import datetime
import shutil

PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
DB_DIR = os.path.join(PROJECT_ROOT, "db")
CONCAT_DIR = os.path.join(DB_DIR, "concat")
SUMMARY_LOG = os.path.join(PROJECT_ROOT, "summary.log")
COMBINED_FASTA_FINAL = os.path.join(PROJECT_ROOT, "combined_fasta.fasta")  # Changed target

def log(msg):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {msg}"
    print(line)
    with open(SUMMARY_LOG, "a") as f:
        f.write(line + "\n")

def run_cmd(cmd, check=True):
    log(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result

# -----------------------------
# Download placeholder functions
# -----------------------------
def download_archaea():
    log("📦 Downloaded archaea genomes (placeholder)")

def download_bacteria():
    log("📦 Downloaded bacteria genomes (placeholder)")

def download_fungi():
    log("📦 Downloaded fungi genomes (placeholder)")

def download_virus():
    log("📦 Downloaded virus genomes (placeholder)")

def download_plants():
    log("📦 Downloaded plant genomes (placeholder)")

DOWNLOAD_FUNCTIONS = {
    "archaea": download_archaea,
    "bacteria": download_bacteria,
    "fungi": download_fungi,
    "virus": download_virus,
    "plants": download_plants,
}

# -----------------------------
# Concatenate genomes
# -----------------------------
def concat_genomes():
    if not os.path.exists(CONCAT_DIR):
        os.makedirs(CONCAT_DIR)
    genome_files = []
    for f in os.listdir(DB_DIR):
        if f.endswith((".fna", ".fa", ".fasta")):
            genome_files.append(os.path.join(DB_DIR, f))
    if not genome_files:
        log("❌ No genome files found to concatenate")
        return
    log(f"Concatenating {len(genome_files)} genome files...")
    concat_temp = os.path.join(CONCAT_DIR, "combined_temp.fasta")
    with open(concat_temp, "w") as out_f:
        for i, fpath in enumerate(genome_files, 1):
            with open(fpath) as in_f:
                out_f.write(in_f.read())
            log(f"  [{i}/{len(genome_files)}] {os.path.basename(fpath)}")
    # Move to final destination (blastdbbuilder root)
    shutil.move(concat_temp, COMBINED_FASTA_FINAL)
    log(f"✅ Concatenation done. File moved to {COMBINED_FASTA_FINAL}")

# -----------------------------
# Build BLAST DB
# -----------------------------
def build_blastdb():
    if not os.path.exists(COMBINED_FASTA_FINAL):
        log(f"❌ Combined FASTA not found: {COMBINED_FASTA_FINAL}")
        return
    blastdb_dir = os.path.join(PROJECT_ROOT, "blastnDB")
    os.makedirs(blastdb_dir, exist_ok=True)
    cmd = [
        "makeblastdb",
        "-in", COMBINED_FASTA_FINAL,
        "-dbtype", "nucl",
        "-out", os.path.join(blastdb_dir, "combined_db"),
    ]
    try:
        run_cmd(cmd)
        log("✅ BLAST DB build completed successfully")
    except subprocess.CalledProcessError:
        log("❌ BLAST DB build failed")

# -----------------------------
# CLI
# -----------------------------
def main():
    parser = argparse.ArgumentParser(description="BlastDBBuilder CLI")
    parser.add_argument("--download", action="store_true", help="Download selected genome groups")
    parser.add_argument("--archaea", action="store_true", help="Download archaea genomes")
    parser.add_argument("--bacteria", action="store_true", help="Download bacteria genomes")
    parser.add_argument("--fungi", action="store_true", help="Download fungi genomes")
    parser.add_argument("--virus", action="store_true", help="Download virus genomes")
    parser.add_argument("--plants", action="store_true", help="Download plant genomes")
    parser.add_argument("--concat", action="store_true", help="Concatenate downloaded genomes")
    parser.add_argument("--build", action="store_true", help="Build BLAST DB from concatenated genomes")
    args = parser.parse_args()

    # Handle downloads
    if args.download:
        any_selected = False
        for group, func in DOWNLOAD_FUNCTIONS.items():
            if getattr(args, group):
                any_selected = True
                func()
        if not any_selected:
            log("⚠️  No genome groups selected for download. Use with --archaea, --bacteria, etc.")

    # Handle concatenation
    if args.concat:
        concat_genomes()

    # Handle BLAST DB build
    if args.build:
        build_blastdb()

if __name__ == "__main__":
    main()
