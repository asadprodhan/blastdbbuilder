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
import glob
import shutil

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
# Utility to write to master summary.log
# -----------------------------
def write_summary(summary_log, message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(summary_log, "a") as f:
        f.write(f"[{timestamp}] {message}\n")

# -----------------------------
# Ensure container exists, otherwise download
# -----------------------------
def ensure_container(container_dir, name, image):
    """Ensure a Singularity container exists in db/containers, otherwise download it."""
    os.makedirs(container_dir, exist_ok=True)
    container_path = os.path.join(container_dir, name)
    if not os.path.isfile(container_path):
        print(f"📦 Downloading container: {name}")
        run_cmd(["singularity", "pull", container_path, image])
    return container_path

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
            writer.writerow([cols[0], cols[1], cols[2], cols[4], cols[7]])

# -----------------------------
# Download genomes for a group
# -----------------------------
def download_group(group_name, assembly_url, db_dir, container_dir, summary_log):
    print(f"\n📂 Downloading {group_name} genomes into {os.path.join(db_dir, group_name)} ...")
    group_dir = os.path.join(db_dir, group_name)
    os.makedirs(group_dir, exist_ok=True)

    # Step 1: Download assembly_summary.txt
    assembly_file = os.path.join(group_dir, "assembly_summary.txt")
    print(f"Downloading assembly_summary.txt for {group_name}...")
    try:
        run_cmd(["wget", "-O", assembly_file, assembly_url])
    except subprocess.CalledProcessError:
        write_summary(summary_log, f"❌ Failed to download assembly_summary.txt for {group_name}")
        return

    # Step 2: Parse assembly_summary.txt and write CSV
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    csv_file = os.path.join(group_dir, f"{group_name}_genomes_{date_str}.csv")
    create_csv_from_summary(assembly_file, csv_file, group_name)
    write_summary(summary_log, f"✅ Created CSV for {group_name}: {csv_file}")

    # Step 3: Ensure NCBI Datasets container exists
    datasets_container = ensure_container(
        container_dir,
        "ncbi-datasets-cli.sif",
        "docker://staphb/ncbi-datasets:latest"
    )
    datasets_exec = f"singularity exec {datasets_container} datasets"

    # Step 4: Download genomes
    with open(csv_file) as f:
        reader = csv.reader(f)
        for row in reader:
            accession = row[0]
            if not accession:
                continue
            fasta_files = glob.glob(os.path.join(group_dir, f"{accession}*.fna")) + \
                          glob.glob(os.path.join(group_dir, f"{accession}*.fa")) + \
                          glob.glob(os.path.join(group_dir, f"{accession}*.fasta"))
            if fasta_files:
                print(f"Skipping {accession} (already downloaded)")
                continue

            zip_file = os.path.join(group_dir, f"{accession}.zip")
            print(f"Downloading: {accession}")
            try:
                run_cmd(datasets_exec.split() + ["download", "genome", "accession", accession, "--filename", zip_file])
            except subprocess.CalledProcessError:
                write_summary(summary_log, f"❌ Error downloading {accession}")
                continue

            # Extract genome
            try:
                run_cmd(["unzip", "-o", zip_file, "-d", group_dir])
            except subprocess.CalledProcessError:
                write_summary(summary_log, f"❌ Error extracting {zip_file}")
                continue

            # Move .fna/.fa/.fasta files
            nested_dir = os.path.join(group_dir, "ncbi_dataset", "data", accession)
            if os.path.isdir(nested_dir):
                for f in os.listdir(nested_dir):
                    if f.endswith((".fna", ".fa", ".fasta")):
                        shutil.move(os.path.join(nested_dir, f), os.path.join(group_dir, f))
                shutil.rmtree(os.path.join(group_dir, "ncbi_dataset"), ignore_errors=True)
            os.remove(zip_file)
            write_summary(summary_log, f"✅ Downloaded {accession}")

    write_summary(summary_log, f"✅ All genomes processed for {group_name}.")

# -----------------------------
# Concatenate genomes
# -----------------------------
def concat_genomes(db_dir, summary_log):
    concat_dir = os.path.join(db_dir, "concat")
    os.makedirs(concat_dir, exist_ok=True)
    output_fasta = os.path.join(concat_dir, "combined.fasta")

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

    # Move concatenated file one level up
    project_root = os.path.abspath(os.path.join(db_dir, ".."))
    final_fasta = os.path.join(project_root, "combined_fasta.fasta")
    shutil.move(output_fasta, final_fasta)
    shutil.rmtree(concat_dir, ignore_errors=True)

    # Delete all subdirectories in db/ except containers
    for sub in os.listdir(db_dir):
        sub_path = os.path.join(db_dir, sub)
        if os.path.isdir(sub_path) and sub != "containers":
            shutil.rmtree(sub_path, ignore_errors=True)

    write_summary(summary_log, f"✅ Concatenated {len(fasta_files)} files, {total_sequences} sequences into {final_fasta}")
    print(f"✅ Concatenation done. File moved to {final_fasta}")
    return final_fasta

# -----------------------------
# Build BLAST database
# -----------------------------
def build_blast_db(fasta_file, summary_log):
    if not fasta_file or not os.path.isfile(fasta_file):
        print("❌ FASTA file for BLAST DB not found.")
        return

    project_root = os.path.dirname(fasta_file)
    blast_dir = os.path.join(project_root, "blastdb")
    os.makedirs(blast_dir, exist_ok=True)

    # Ensure BLAST container exists
    container_dir = os.path.join(project_root, "db", "containers")
    blast_container = ensure_container(
        container_dir,
        "ncbi-blast_2.16.0.sif",
        "docker://staphb/ncbi-blast:2.16.0"
    )

    # Auto-detect FASTA file extensions
    fasta_file_name = os.path.basename(fasta_file)
    db_prefix = os.path.join(blast_dir, os.path.splitext(fasta_file_name)[0])

    print(f"Building BLAST database for {fasta_file} ...")
    write_summary(summary_log, f"➡️ Starting BLAST DB build for {fasta_file}")

    cmd = [
        "singularity", "exec", blast_container,
        "makeblastdb",
        "-in", fasta_file,
        "-dbtype", "nucl",
        "-out", db_prefix
    ]

    run_cmd(cmd)
    write_summary(summary_log, f"✅ BLAST DB built: {db_prefix}")
    print(f"✅ BLAST database built at {db_prefix}")

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
    parser.add_argument("--virus", action="store_true", help="Include Virus genomes (all)")
    parser.add_argument("--plants", action="store_true", help="Include Plant genomes")
    args = parser.parse_args()

    summary_log = os.path.join(os.path.abspath(os.getcwd()), "summary.log")
    db_dir = os.path.join(os.path.abspath(os.getcwd()), "db")
    container_dir = os.path.join(db_dir, "containers")
    os.makedirs(db_dir, exist_ok=True)
    os.makedirs(container_dir, exist_ok=True)

    # -----------------------------
    # Downloads
    # -----------------------------
    if args.download:
        groups = []
        if args.archaea:
            groups.append(("archaea", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/archaea/assembly_summary.txt"))
        if args.bacteria:
            groups.append(("bacteria", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/assembly_summary.txt"))
        if args.fungi:
            groups.append(("fungi", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/fungi/assembly_summary.txt"))
        if args.virus:
            groups.append(("virus", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/viral/assembly_summary.txt"))
        if args.plants:
            groups.append(("plants", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/plant/assembly_summary.txt"))

        for name, url in groups:
            download_group(name, url, db_dir, container_dir, summary_log)

    # -----------------------------
    # Concatenate
    # -----------------------------
    final_fasta = None
    if args.concat:
        final_fasta = concat_genomes(db_dir, summary_log)

    # -----------------------------
    # Build BLAST DB
    # -----------------------------
    if args.build:
        if not final_fasta:
            # Attempt to find concatenated FASTA one level up
            project_root = os.path.abspath(os.path.join(db_dir, ".."))
            candidate = os.path.join(project_root, "combined_fasta.fasta")
            if os.path.isfile(candidate):
                final_fasta = candidate
        build_blast_db(final_fasta, summary_log)

    # -----------------------------
    # Citation
    # -----------------------------
    if args.citation:
        print("blastdbbuilder (Asad Prodhan, 2025). Please cite as needed.")

if __name__ == "__main__":
    main()
