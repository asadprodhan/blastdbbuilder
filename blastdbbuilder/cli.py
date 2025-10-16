#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys

# -----------------------------
# Define genome groups
# -----------------------------
GENOME_GROUPS = {
    "archaea": "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/archaea/assembly_summary.txt",
    "bacteria": "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/assembly_summary.txt",
    "fungi": "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/fungi/assembly_summary.txt",
    "virus": "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/viral/assembly_summary.txt"
}

def run_cmd(cmd, cwd=None):
    """Run a shell command with error checking"""
    try:
        subprocess.run(cmd, shell=True, check=True, cwd=cwd)
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running command: {cmd}")
        sys.exit(1)

def download_group(group, base_dir):
    """Download genomes for a single group"""
    print(f"\n📂 Downloading {group} genomes into {base_dir}/db/{group} ...")
    group_dir = os.path.join(base_dir, "db", group)
    os.makedirs(group_dir, exist_ok=True)

    # Containers directory shared across groups
    container_dir = os.path.join(base_dir, "db", "containers")
    os.makedirs(container_dir, exist_ok=True)
    datasets_container = os.path.join(container_dir, "ncbi-datasets-cli.sif")
    datasets_image = "docker://staphb/ncbi-datasets:latest"

    if not os.path.isfile(datasets_container):
        print("📦 Pulling NCBI Datasets container...")
        run_cmd(f"singularity pull {datasets_container} {datasets_image}")

    datasets_exec = f"singularity exec {datasets_container} datasets"

    # Download assembly summary
    assembly_file = os.path.join(group_dir, "assembly_summary.txt")
    print(f"Downloading assembly_summary.txt for {group}...")
    run_cmd(f"wget -O {assembly_file} {GENOME_GROUPS[group]}")

    # Extract reference genomes
    date_str = subprocess.getoutput("date +%F")
    ref_csv = os.path.join(group_dir, f"{group}_reference_genome_{date_str}.csv")
    awk_cmd = f"""awk -F "\\t" '$0 !~ /^#/ && $5=="reference genome" {{print $1","$2","$3","$5","$8}}' {assembly_file} > {ref_csv}"""
    run_cmd(awk_cmd)

    # Split CSV into 5000-line chunks
    run_cmd(f"split -l 5000 -d --additional-suffix=.csv {ref_csv} {group_dir}/temp_part_")
    for i, f in enumerate(sorted(os.listdir(group_dir))):
        if f.startswith("temp_part_") and f.endswith(".csv"):
            os.rename(os.path.join(group_dir, f),
                      os.path.join(group_dir, f"{group}_reference_genome_part{i+1}_{date_str}.csv"))

    # Process each CSV sequentially
    for metadata in sorted(os.listdir(group_dir)):
        if metadata.startswith(f"{group}_reference_genome_part") and metadata.endswith(".csv"):
            metadata_path = os.path.join(group_dir, metadata)
            with open(metadata_path) as fh:
                for line in fh:
                    accession = line.strip().split(",")[0]
                    if not accession:
                        continue
                    zip_file = os.path.join(group_dir, f"{accession}.zip")
                    print(f"Downloading {accession} ...")
                    run_cmd(f"{datasets_exec} download genome accession {accession} --filename {zip_file}")
                    print(f"Extracting {zip_file} into {group_dir} ...")
                    run_cmd(f"unzip -o {zip_file} -d {group_dir}")
                    # Move all .fna to group_dir
                    run_cmd(f"find {group_dir}/ncbi_dataset -name '*.fna' -exec mv {{}} {group_dir}/ \\;")
                    # Cleanup zip and extraction dirs
                    run_cmd(f"rm -rf {zip_file} {group_dir}/ncbi_dataset")
    print(f"✅ Finished downloading {group} genomes. Files are in {group_dir}\n")

# -----------------------------
# CLI arguments
# -----------------------------
def main():
    parser = argparse.ArgumentParser(
        description="blastdbbuilder: Automated genome download, concatenation, and BLAST database builder"
    )
    parser.add_argument("--download", action="store_true", help="Download genomes for selected groups")
    parser.add_argument("--concat", action="store_true", help="Concatenate all genomes into one FASTA")
    parser.add_argument("--build", action="store_true", help="Build BLAST database from concatenated FASTA")
    parser.add_argument("--archaea", action="store_true", help="Include Archaea genomes")
    parser.add_argument("--bacteria", action="store_true", help="Include Bacteria genomes")
    parser.add_argument("--fungi", action="store_true", help="Include Fungi genomes")
    parser.add_argument("--virus", action="store_true", help="Include Virus genomes")

    args = parser.parse_args()

    base_dir = os.getcwd()
    selected_groups = [g for g in ["archaea", "bacteria", "fungi", "virus"] if getattr(args, g)]

    if args.download:
        if not selected_groups:
            print("⚠️ No group selected. Use --archaea, --bacteria, --fungi, or --virus")
            sys.exit(1)
        for group in selected_groups:
            download_group(group, base_dir)

if __name__ == "__main__":
    main()
