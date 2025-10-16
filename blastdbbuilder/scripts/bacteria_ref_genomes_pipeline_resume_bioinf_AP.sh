#!/bin/bash --login
# ======================================
# Bacterial Reference Genome Downloader (RESUME mode)
# ======================================

DATE=$(date +%F)  # YYYY-MM-DD format

# -----------------------------
# 1. Singularity + NCBI Datasets setup
# -----------------------------
export SINGULARITY_CACHEDIR="$HOME/.singularity/cache"
mkdir -p "$SINGULARITY_CACHEDIR"

CONTAINER_DIR="$HOME/containers"
DATASETS_CONTAINER="$CONTAINER_DIR/ncbi-datasets-cli.sif"
DATASETS_IMAGE="docker://staphb/ncbi-datasets:latest"
mkdir -p "$CONTAINER_DIR"

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
        if ls ${accession}*.fna 1> /dev/null 2>&1; then
            echo "Skipping ${accession} (already downloaded)"
            continue
        fi

        echo ""
        echo "Downloading: ${accession}"

        if ! $datasets_exec download genome accession "${accession}" --filename "${accession}.zip"; then
            echo "Error downloading ${accession}"
            continue
        fi

        echo "Extracting ${accession}.zip"
        if ! unzip -o "${accession}.zip"; then
            echo "Error extracting ${accession}.zip"
            rm -f "${accession}.zip"
            continue
        fi

        cd "ncbi_dataset/data/${accession}" || { echo "Error: Directory not found for ${accession}"; continue; }

        if ls *.fna 1> /dev/null 2>&1; then
            echo "Moving ${accession} fasta file into working directory"
            mv *.fna ../../../
        else
            echo "No .fna files found for ${accession}"
        fi

        cd "../../../" || exit
        rm -r "${accession}.zip" ncbi_dataset *.md

        echo "Download completed: ${accession}"
        echo ""
    done < "${metadata}"

    echo "Finished processing ${metadata}"
    echo ""
done

echo "All CSV files have been processed."
