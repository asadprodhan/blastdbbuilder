#!/bin/bash --login
# ================================================================
# download_archaea.sh
# Author: Asad Prodhan
# Date: 2025-10-16
# Description: Download Archaea reference genomes into db/archaea
# ================================================================

set -euo pipefail

# -----------------------------
# 0. Output directory setup
# -----------------------------
OUTPUT_DIR="${1:-$PWD}"
ARCHAEA_DIR="$OUTPUT_DIR/db/archaea"
mkdir -p "$ARCHAEA_DIR"

# -----------------------------
# 1. Get current date
# -----------------------------
DATE=$(date +%F)  # YYYY-MM-DD

# -----------------------------
# 2. Download assembly_summary.txt
# -----------------------------
echo "Downloading assembly_summary.txt..."
ASSEMBLY_SUMMARY="$ARCHAEA_DIR/assembly_summary.txt"
if wget -O "$ASSEMBLY_SUMMARY" https://ftp.ncbi.nlm.nih.gov/genomes/refseq/archaea/assembly_summary.txt; then
    echo "✅ Download successful."
else
    echo "❌ Download failed. Exiting."
    exit 1
fi

# -----------------------------
# 3. Extract reference genomes into CSV
# -----------------------------
OUTPUT_CSV="$ARCHAEA_DIR/archaeal_reference_genome_${DATE}.csv"
echo "Filtering reference genomes and extracting columns..."
awk -F "\t" '$0 !~ /^#/ && $5=="reference genome" {print $1","$2","$3","$5","$8}' "$ASSEMBLY_SUMMARY" \
    > "$OUTPUT_CSV"

LINES=$(wc -l < "$OUTPUT_CSV")
if [ "$LINES" -eq 0 ]; then
    echo "No reference genomes found. Exiting."
    exit 1
fi
echo "Extracted $LINES reference genomes into $OUTPUT_CSV"

# -----------------------------
# 4. Split CSV into 5000-line chunks
# -----------------------------
echo "Splitting CSV into 5000-line chunks..."
cd "$ARCHAEA_DIR"
split -l 5000 -d --additional-suffix=".csv" "$(basename "$OUTPUT_CSV")" temp_part_

# Rename sequentially with date
n=1
for f in temp_part_*.csv; do
    mv "$f" "archaeal_reference_genome_part${n}_${DATE}.csv"
    ((n++))
done
echo "Done! Generated $(ls archaeal_reference_genome_part*_${DATE}.csv | wc -l) files."

# -----------------------------
# 5. Singularity + NCBI Datasets setup
# -----------------------------
export SINGULARITY_CACHEDIR="$ARCHAEA_DIR/.singularity/cache"
mkdir -p "$SINGULARITY_CACHEDIR"

CONTAINER_DIR="$ARCHAEA_DIR/containers"
DATASETS_CONTAINER="$CONTAINER_DIR/ncbi-datasets-cli.sif"
DATASETS_IMAGE="docker://staphb/ncbi-datasets:latest"
mkdir -p "$CONTAINER_DIR"

if [ ! -f "$DATASETS_CONTAINER" ]; then
    echo "Downloading NCBI Datasets container..."
    singularity pull "$DATASETS_CONTAINER" "$DATASETS_IMAGE"
fi

datasets_exec="singularity exec $DATASETS_CONTAINER datasets"

# -----------------------------
# 6. Process split CSV files
# -----------------------------
for metadata in archaeal_reference_genome_part*_${DATE}.csv; do
    echo "======================================"
    echo " Processing CSV file: ${metadata}"
    echo "======================================"

    while IFS=, read -r accession rest; do
        [ -z "$accession" ] && continue

        echo ""
        echo "Downloading genome: ${accession}"

        ZIP_FILE="$ARCHAEA_DIR/${accession}.zip"

        # Download genome
        if ! $datasets_exec download genome accession "${accession}" --filename "$ZIP_FILE"; then
            echo "❌ Error downloading ${accession}"
            continue
        fi

        # Extract genome directly into ARCHAEA_DIR
        echo "Extracting $ZIP_FILE into $ARCHAEA_DIR"
        if ! unzip -o "$ZIP_FILE" -d "$ARCHAEA_DIR"; then
            echo "❌ Error extracting $ZIP_FILE"
            rm -f "$ZIP_FILE"
            continue
        fi

        # Move .fna files to ARCHAEA_DIR
        find "$ARCHAEA_DIR/ncbi_dataset/data/$accession" -name "*.fna" -exec mv {} "$ARCHAEA_DIR/" \;

        # Cleanup temporary extraction
        rm -rf "$ARCHAEA_DIR/ncbi_dataset"
        rm -f "$ZIP_FILE"
        rm -f "$ARCHAEA_DIR"/*.md

        echo "✅ Download completed: ${accession}"
        echo ""
    done < "$metadata"

    echo "Finished processing ${metadata}"
    echo ""
done

echo "All CSV files have been processed."
echo "✅ Archaea reference genomes are now in $ARCHAEA_DIR"
