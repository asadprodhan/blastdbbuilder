#!/usr/bin/env python3
import argparse
import os
import subprocess
from datetime import date

def run_cmd(cmd, cwd=None):
    """Run a shell command, exit on failure"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    if result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")

def prepare_container(container_dir):
    os.makedirs(container_dir, exist_ok=True)
    datasets_container = os.path.join(container_dir, "ncbi-datasets-cli.sif")
    datasets_image = "docker://staphb/ncbi-datasets:latest"
    if not os.path.exists(datasets_container):
        run_cmd(["singularity", "pull", datasets_container, datasets_image])
    return datasets_container

def download_group(group_name, ftp_path, db_dir, container_dir):
    group_dir = os.path.join(db_dir, group_name)
    os.makedirs(group_dir, exist_ok=True)
    
    # Assembly summary
    assembly_file = os.path.join(group_dir, "assembly_summary.txt")
    print(f"📂 Downloading {group_name} genomes into {group_dir} ...")
    print(f"Downloading assembly_summary.txt for {group_name}...")
    run_cmd(["wget", "-O", assembly_file, ftp_path])
    
    # Create reference genome CSV
    today = date.today().strftime("%Y-%m-%d")
    csv_file = os.path.join(group_dir, f"{group_name}_reference_genome_{today}.csv")
    
    if group_name.lower() in ["virus"]:
        # virus: all assemblies
        awk_cmd = f"$0 !~ /^#/ {{print $1\",\"$2\",\"$3\",\"$5\",\"$8}}"
    else:
        # archaea/bacteria/fungi: reference genomes only
        awk_cmd = f"$0 !~ /^#/ && $5==\"reference genome\" {{print $1\",\"$2\",\"$3\",\"$5\",\"$8}}"
    
    run_cmd(["awk", "-F", "\t", awk_cmd, assembly_file, ">", csv_file], cwd=group_dir, shell=True)
    
    # Split CSV into chunks of 5000
    run_cmd(["split", "-l", "5000", "-d", "--additional-suffix=.csv", csv_file, os.path.join(group_dir, f"{group_name}_reference_genome_part_")])
    
    # Singularity datasets CLI
    datasets_container = os.path.join(container_dir, "ncbi-datasets-cli.sif")
    datasets_exec = ["singularity", "exec", datasets_container, "datasets"]
    
    # Process CSV parts sequentially
    for part_file in sorted([f for f in os.listdir(group_dir) if f.startswith(f"{group_name}_reference_genome_part")]):
        part_path = os.path.join(group_dir, part_file)
        print(f"======================================")
        print(f" Processing CSV file: {part_file}")
        print(f"======================================")
        with open(part_path) as f:
            for line in f:
                accession = line.strip().split(",")[0]
                if not accession:
                    continue
                fasta_files = [f for f in os.listdir(group_dir) if f.startswith(accession) and f.endswith(".fna")]
                if fasta_files:
                    print(f"Skipping {accession} (already downloaded)")
                    continue
                zip_file = os.path.join(group_dir, f"{accession}.zip")
                run_cmd(datasets_exec + ["download", "genome", "accession", accession, "--filename", zip_file])
                # unzip into group_dir
                run_cmd(["unzip", "-o", zip_file, "-d", group_dir])
                os.remove(zip_file)
                # move all .fna files from extracted ncbi_dataset/data/* to group_dir
                ncbi_data_dir = os.path.join(group_dir, "ncbi_dataset", "data", accession)
                if os.path.exists(ncbi_data_dir):
                    for f in os.listdir(ncbi_data_dir):
                        if f.endswith(".fna"):
                            os.rename(os.path.join(ncbi_data_dir, f), os.path.join(group_dir, f))
                    # clean up extracted folders
                    subprocess.run(["rm", "-rf", os.path.join(group_dir, "ncbi_dataset")])
                print(f"Download completed: {accession}")

def main():
    parser = argparse.ArgumentParser(description="blastdbbuilder: Automated genome download and BLAST DB builder")
    parser.add_argument("--download", action="store_true", help="Download genomes for selected groups")
    parser.add_argument("--archaea", action="store_true", help="Include Archaea genomes")
    parser.add_argument("--bacteria", action="store_true", help="Include Bacteria genomes")
    parser.add_argument("--fungi", action="store_true", help="Include Fungi genomes")
    parser.add_argument("--virus", action="store_true", help="Include Virus genomes")
    args = parser.parse_args()
    
    if not args.download:
        print("Nothing to do. Use --download with one or more groups")
        return
    
    # db root
    db_dir = os.path.join(os.getcwd(), "db")
    container_dir = os.path.join(db_dir, "containers")
    os.makedirs(db_dir, exist_ok=True)
    
    if args.archaea:
        download_group("archaea", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/archaea/assembly_summary.txt", db_dir, container_dir)
    if args.bacteria:
        download_group("bacteria", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/assembly_summary.txt", db_dir, container_dir)
    if args.fungi:
        download_group("fungi", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/fungi/assembly_summary.txt", db_dir, container_dir)
    if args.virus:
        download_group("virus", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/viral/assembly_summary.txt", db_dir, container_dir)
    
    print("✅ All requested downloads completed.")

if __name__ == "__main__":
    main()
