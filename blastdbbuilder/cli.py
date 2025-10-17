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
            if group_name.lower() in ["archaea", "bacteria", "fungi", "plants"]:
                if cols[4] != "reference genome":
                    continue
            # columns: 1,2,3,5,8
            writer.writerow([cols[0], cols[1], cols[2], cols[4], cols[7]])

# -----------------------------
# Download genomes for a group
# -----------------------------
def download_group(group_name, assembly_url, db_dir, container_dir, summary):
    """Download reference genomes for a specific group"""
    group_dir = os.path.join(db_dir, group_name)
    os.makedirs(group_dir, exist_ok=True)

    summary[group_name] = {"downloaded": 0, "total": 0}

    print(f"\n📂 Downloading {group_name} genomes into {group_dir} ...")

    # Step 1: Download assembly_summary.txt
    assembly_file = os.path.join(group_dir, "assembly_summary.txt")
    print(f"Downloading assembly_summary.txt for {group_name}...")
    run_cmd(["wget", "-O", assembly_file, assembly_url])

    # Step 2: Parse assembly_summary.txt and write CSV
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    csv_file = os.path.join(group_dir, f"{group_name}_reference_genome_{date_str}.csv")
    create_csv_from_summary(assembly_file, csv_file, group_name)
    print(f"✅ Finished creating CSV: {csv_file}")

    # Count total genomes
    with open(csv_file) as f:
        total_genomes = sum(1 for _ in f)
    summary[group_name]["total"] = total_genomes
    print(f"Total reference genomes found for {group_name}: {total_genomes}")

    # -----------------------------
    # Step 3: Setup NCBI Datasets container
    # -----------------------------
    os.makedirs(container_dir, exist_ok=True)
    datasets_container = os.path.join(container_dir, "ncbi-datasets-cli.sif")
    datasets_image = "docker://staphb/ncbi-datasets:latest"
    if not os.path.isfile(datasets_container):
        print("Downloading NCBI Datasets container...")
        run_cmd(["singularity", "pull", datasets_container, datasets_image])

    datasets_exec = f"singularity exec {datasets_container} datasets"

    # Step 4: Process CSV and download genomes
    print(f"Downloading genomes for {group_name} ...")
    with open(csv_file) as f:
        reader = csv.reader(f)
        for idx, row in enumerate(reader, 1):
            accession = row[0]
            if not accession:
                continue

            fasta_file = os.path.join(group_dir, f"{accession}.fna")
            if os.path.isfile(fasta_file):
                print(f"[{group_name}] Skipping {accession} (already downloaded)")
                summary[group_name]["downloaded"] += 1
                continue

            zip_file = os.path.join(group_dir, f"{accession}.zip")
            print(f"[{group_name}] Downloading {idx}/{total_genomes}: {accession}")
            try:
                run_cmd(datasets_exec.split() + ["download", "genome", "accession", accession, "--filename", zip_file])
            except subprocess.CalledProcessError:
                print(f"Error downloading {accession}, skipping.")
                continue

            # Extract genome
            try:
                run_cmd(["unzip", "-o", zip_file, "-d", group_dir])
            except subprocess.CalledProcessError:
                print(f"Error extracting {zip_file}, skipping.")
                continue

            # Move .fna files from nested ncbi_dataset/data/... to group_dir
            nested_dir = os.path.join(group_dir, "ncbi_dataset", "data", accession)
            if os.path.isdir(nested_dir):
                for fna in os.listdir(nested_dir):
                    if fna.endswith(".fna"):
                        os.rename(os.path.join(nested_dir, fna), os.path.join(group_dir, fna))
                # Cleanup
                subprocess.run(["rm", "-rf", os.path.join(group_dir, "ncbi_dataset")])
                os.remove(zip_file)

            summary[group_name]["downloaded"] += 1

    print(f"✅ Completed downloads for {group_name} ({summary[group_name]['downloaded']} genomes).")

# -----------------------------
# Concatenate genomes
# -----------------------------
def concatenate_genomes(db_dir, summary):
    concat_dir = os.path.join(db_dir, "concat")
    os.makedirs(concat_dir, exist_ok=True)

    all_fna_files = []
    for group in ["archaea","bacteria","fungi","virus","plants"]:
        group_dir = os.path.join(db_dir, group)
        if os.path.isdir(group_dir):
            for fna in os.listdir(group_dir):
                if fna.endswith(".fna"):
                    all_fna_files.append(os.path.join(group_dir, fna))
                    # Move to concat_dir
                    os.rename(os.path.join(group_dir, fna), os.path.join(concat_dir, fna))

    combined_fasta = os.path.join(concat_dir, "combined_fasta.fna")
    print(f"\n📂 Concatenating all genomes into {combined_fasta} ...")
    with open(combined_fasta, "w") as outfile:
        for idx, fna in enumerate(sorted(os.listdir(concat_dir)), 1):
            if fna.endswith(".fna"):
                with open(os.path.join(concat_dir, fna)) as infile:
                    outfile.write(infile.read())
                print(f"[Concat] {idx}/{len(all_fna_files)} files processed", end="\r")
    print(f"\n✅ Concatenation completed: {combined_fasta}")
    summary["concatenated"] = len(all_fna_files)

    return combined_fasta

# -----------------------------
# Write master summary log
# -----------------------------
def write_summary_log(summary):
    log_file = "summary.log"
    date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "w") as f:
        f.write(f"Master summary for blastdbbuilder run: {date_str}\n\n")
        for group in ["archaea","bacteria","fungi","virus","plants"]:
            total = summary.get(group, {}).get("total", 0)
            downloaded = summary.get(group, {}).get("downloaded", 0)
            f.write(f"Total genomes downloaded from {group} on {date_str}: {downloaded} / {total}\n")
        concatenated = summary.get("concatenated", 0)
        f.write(f"\nConcatenated genomes: {concatenated}\n")
        f.write(f"\nDatabase build: Placeholder (not yet executed)\n")
        f.write(f"Database build timestamp: N/A\n")
        f.write("\nRUNNING PROGRESS tracked in stdout.\n")
    print(f"\n✅ Summary log written to {log_file}")

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
    parser.add_argument("--plants", action="store_true", help="Include Plants genomes")

    args = parser.parse_args()

    db_dir = os.path.join(os.getcwd(), "db")
    container_dir = os.path.join(db_dir, "containers")
    os.makedirs(db_dir, exist_ok=True)

    summary = {}

    # -----------------------------
    # Step 1: Download genomes
    # -----------------------------
    if args.download:
        if args.archaea:
            download_group("archaea", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/archaea/assembly_summary.txt", db_dir, container_dir, summary)
        if args.bacteria:
            download_group("bacteria", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/assembly_summary.txt", db_dir, container_dir, summary)
        if args.fungi:
            download_group("fungi", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/fungi/assembly_summary.txt", db_dir, container_dir, summary)
        if args.virus:
            download_group("virus", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/viral/assembly_summary.txt", db_dir, container_dir, summary)
        if args.plants:
            download_group("plants", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/plants/assembly_summary.txt", db_dir, container_dir, summary)

    # -----------------------------
    # Step 2: Concatenate genomes
    # -----------------------------
    if args.concat:
        combined_fasta = concatenate_genomes(db_dir, summary)
        print(f"Combined FASTA file: {combined_fasta}")

    # -----------------------------
    # Step 3: Build database placeholder
    # -----------------------------
    if args.build:
        print("\n🚧 Database build functionality placeholder")
        print(f"Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        # TODO: Implement makeblastdb call here

    # -----------------------------
    # Step 4: Summary log
    # -----------------------------
    write_summary_log(summary)

    # -----------------------------
    # Step 5: Citation
    # -----------------------------
    if args.citation:
        print("blastdbbuilder: please cite NCBI Datasets and BLAST+ if used.")

if __name__ == "__main__":
    main()
