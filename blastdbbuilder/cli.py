#!/usr/bin/env python3
# blastdbbuilder/cli.py
# ======================================
# Automated genome download, concatenation, and BLAST DB builder
# ======================================

import argparse
import os
import sys
import subprocess
import datetime
import csv
from pathlib import Path

# -----------------------------
# Utility to run shell commands
# -----------------------------
def run_cmd(cmd, cwd=None):
    """Run a command and print stdout/stderr"""
    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print("❌ Command failed:", " ".join(cmd))
        print(result.stderr)
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result.stdout

# -----------------------------
# Create CSV from assembly_summary.txt
# -----------------------------
def create_csv_from_summary(assembly_file, csv_file, group_name):
    """Parse assembly_summary.txt and write CSV"""
    with open(assembly_file) as infile, open(csv_file, "w", newline="") as outfile:
        writer = csv.writer(outfile)
        for line in infile:
            if line.startswith("#"):
                continue
            cols = line.strip().split("\t")

            # Only filter reference genomes for certain groups
            if group_name.lower() in ["archaea", "bacteria", "fungi", "plants"]:
                if cols[4] != "reference genome":
                    continue
            # Virus includes all genomes

            # columns: 1,2,3,5,8
            writer.writerow([cols[0], cols[1], cols[2], cols[4], cols[7]])

# -----------------------------
# Download genomes for a group
# -----------------------------
def download_group(group_name, assembly_url, db_dir, container_dir, summary):
    """Download genomes for a specific group"""
    group_dir = os.path.join(db_dir, group_name)
    os.makedirs(group_dir, exist_ok=True)

    print(f"\n📂 Downloading {group_name} genomes into {group_dir} ...")
    summary[group_name] = {"downloaded": 0, "total": 0}

    # Step 1: Download assembly_summary.txt
    assembly_file = os.path.join(group_dir, "assembly_summary.txt")
    run_cmd(["wget", "-O", assembly_file, assembly_url])

    # Step 2: Parse assembly_summary.txt and write CSV
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    csv_file = os.path.join(group_dir, f"{group_name}_genomes_{date_str}.csv")
    create_csv_from_summary(assembly_file, csv_file, group_name)
    print(f"✅ Finished creating CSV: {csv_file}")

    # Count total genomes
    with open(csv_file) as f:
        total_genomes = sum(1 for _ in f)
    summary[group_name]["total"] = total_genomes

    # Step 3: Setup NCBI Datasets container
    os.makedirs(container_dir, exist_ok=True)
    datasets_container = os.path.join(container_dir, "ncbi-datasets-cli.sif")
    datasets_image = "docker://staphb/ncbi-datasets:latest"
    if not os.path.isfile(datasets_container):
        print("Downloading NCBI Datasets container...")
        run_cmd(["singularity", "pull", datasets_container, datasets_image])

    datasets_exec = f"singularity exec {datasets_container} datasets"

    # Step 4: Process CSV and download genomes
    with open(csv_file) as f:
        reader = csv.reader(f)
        for i, row in enumerate(reader, start=1):
            accession = row[0]
            if not accession:
                continue

            fasta_file = os.path.join(group_dir, f"{accession}.fna")
            if os.path.isfile(fasta_file):
                print(f"[{group_name}] Skipping {accession} (already downloaded)")
                summary[group_name]["downloaded"] += 1
                continue

            zip_file = os.path.join(group_dir, f"{accession}.zip")
            print(f"[{group_name}] Downloading {accession} ({i}/{total_genomes})")
            try:
                run_cmd(datasets_exec.split() + ["download", "genome", "accession", accession, "--filename", zip_file])
            except subprocess.CalledProcessError:
                print(f"[{group_name}] Error downloading {accession}, skipping.")
                continue

            # Extract genome
            try:
                run_cmd(["unzip", "-o", zip_file, "-d", group_dir])
            except subprocess.CalledProcessError:
                print(f"[{group_name}] Error extracting {zip_file}, skipping.")
                continue

            # Move any genome files (.fna, .fa, .fasta) to group_dir
            nested_dir = os.path.join(group_dir, "ncbi_dataset", "data", accession)
            if os.path.isdir(nested_dir):
                for genome_file in os.listdir(nested_dir):
                    if genome_file.endswith((".fna", ".fa", ".fasta")):
                        os.rename(os.path.join(nested_dir, genome_file), os.path.join(group_dir, genome_file))

            # Cleanup
            subprocess.run(["rm", "-rf", os.path.join(group_dir, "ncbi_dataset")])
            os.remove(zip_file)

            summary[group_name]["downloaded"] += 1

    print(f"✅ Completed downloading genomes for {group_name} ({summary[group_name]['downloaded']}/{total_genomes})")

# -----------------------------
# Concatenate genomes
# -----------------------------
def concatenate_genomes(db_dir, summary):
    concat_dir = os.path.join(db_dir, "concat")
    os.makedirs(concat_dir, exist_ok=True)
    combined_fasta = os.path.join(concat_dir, "combined_fasta.fna")
    total_sequences = 0

    print("\n📂 Concatenating genomes...")
    for group in ["archaea", "bacteria", "fungi", "virus", "plants"]:
        group_dir = os.path.join(db_dir, group)
        if not os.path.isdir(group_dir):
            continue
        genome_files = [f for f in os.listdir(group_dir) if f.endswith((".fna", ".fa", ".fasta"))]
        for gf in genome_files:
            with open(os.path.join(group_dir, gf)) as f_in, open(combined_fasta, "a") as f_out:
                for line in f_in:
                    f_out.write(line)
                    if line.startswith(">"):
                        total_sequences += 1

    print(f"✅ Concatenation complete: {total_sequences} sequences in {combined_fasta}")
    summary["concatenated"] = total_sequences
    return combined_fasta

# -----------------------------
# Master summary log
# -----------------------------
def write_summary_log(summary, combined_fasta=None):
    log_file = os.path.join(os.getcwd(), "summary.log")
    with open(log_file, "w") as f:
        f.write(f"Database Build Summary - {datetime.datetime.now()}\n\n")
        for group in ["archaea", "bacteria", "fungi", "virus", "plants"]:
            info = summary.get(group, {"downloaded":0, "total":0})
            f.write(f"Total genomes downloaded from {group}: {info['downloaded']} out of {info['total']}\n")
        if combined_fasta:
            f.write(f"\nConcatenated genomes: {summary.get('concatenated',0)}\n")
            f.write(f"Combined FASTA file: {combined_fasta}\n")
        f.write("\nDatabase build placeholder: Not yet executed.\n")
    print(f"\n📄 Master summary log written to {log_file}")

# -----------------------------
# Main CLI
# -----------------------------
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
    parser.add_argument("--plants", action="store_true", help="Include Plant genomes")

    args = parser.parse_args()

    db_dir = os.path.join(os.getcwd(), "db")
    container_dir = os.path.join(db_dir, "containers")
    os.makedirs(db_dir, exist_ok=True)

    summary = {}

    # -----------------------------
    # Step 1: Download genomes
    # -----------------------------
    if args.download:
        for group_flag, group_name, url in [
            (args.archaea, "archaea", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/archaea/assembly_summary.txt"),
            (args.bacteria, "bacteria", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/assembly_summary.txt"),
            (args.fungi, "fungi", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/fungi/assembly_summary.txt"),
            (args.virus, "virus", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/viral/assembly_summary.txt"),
            (args.plants, "plants", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/plants/assembly_summary.txt"),
        ]:
            if group_flag:
                download_group(group_name, url, db_dir, container_dir, summary)

    # -----------------------------
    # Step 2: Concatenate genomes
    # -----------------------------
    combined_fasta = None
    if args.concat:
        combined_fasta = concatenate_genomes(db_dir, summary)

    # -----------------------------
    # Step 3: Placeholder for BLAST DB build
    # -----------------------------
    if args.build:
        print("\n🚧 BLAST database build placeholder. Will record timestamp.")
        summary["db_build_time"] = str(datetime.datetime.now())

    # -----------------------------
    # Step 4: Write master summary log
    # -----------------------------
    write_summary_log(summary, combined_fasta)

    if args.citation:
        print("\nblastdbbuilder: please cite NCBI Datasets and BLAST+ if used.")

if __name__ == "__main__":
    main()
