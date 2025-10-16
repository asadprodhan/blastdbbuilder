#!/bin/bash --login
# ======================================
# Bacterial Reference Genome Downloader (RESUME mode)
# ======================================

DATE=$(date +%F)  # YYYY-MM-DD format

# -----------------------------
# 0. Setup output directory
# -----------------------------
BASE_DIR="$PWD"
GROUP_DIR="$BASE_DIR/db/bacteria"
mkdir -p "$GROUP_DIR"

# -----------------------------
# 1. Singularity + NCBI Datasets setup
# -----------------------------
CONTAINER_DIR="$BASE_DIR/db/containers"
mkdir -p "$CONTAINER_DIR"

DATASETS_CONTAINER="$CONTAINER_DIR/ncbi-datasets-cli.sif"
DATASETS_IMAGE="docker://staphb/ncbi-datasets:latest"

if [ ! -f "$DATASETS_CONTAINER" ]; then
  echo "Downloading NCBI Datasets container..."
  singularity pull "$DATASETS_CONTAINER" "$DATASETS_IMAGE"
fi

datasets_exec="singularity exec $DATASETS_CONTAINER datasets"

# -----------------------------
# 2. Resume processing split CSV files
# -----------------------------
for metadata in bacterial_reference_genome_part*.csv; do
    echo "======================================"
    echo " Processing CSV file: ${metadata}"
    echo "======================================"

    while IFS=, read -r accession rest; do
        [ -z "$accession" ] && continue

        # -----------------------------
        # Resume check: skip if fasta already exists
        # -----------------------------
        if ls "$GROUP_DIR/${accession}"*.fna 1> /dev/null 2>&1; then
            echo "Skipping ${accession} (already downloaded)"
            continue
        fi

        echo ""
        echo "Downloading: ${accession}"

        zip_file="$GROUP_DIR/${accession}.zip"
        if ! $datasets_exec download genome accession "${accession}" --filename "$zip_file"; then
            echo "Error downloading ${accession}"
            continue
        fi

        echo "Extracting $zip_file"
        if ! unzip -o "$zip_file" -d "$GROUP_DIR"; then
            echo "Error extracting $zip_file"
            rm -f "$zip_file"
            continue
        fi

        # Move .fna files from extracted directory to GROUP_DIR
        find "$GROUP_DIR/ncbi_dataset" -name "*.fna" -exec mv {} "$GROUP_DIR/" \;

        # Cleanup zip and extraction directories
        rm -rf "$zip_file" "$GROUP_DIR/ncbi_dataset" *.md 2>/dev/null

        echo "Download completed: ${accession}"
        echo ""
    done < "$metadata"

    echo "Finished processing ${metadata}"
    echo ""
done

echo "All CSV files have been processed into $GROUP_DIR."
