#!/bin/bash --login
# ======================================
# Plant Reference Genome Downloader (RESUME mode)
# CLI-consistent version
# ======================================

set -euo pipefail

# -----------------------------
# 0. Setup
# -----------------------------
DATE=$(date +%F)
BASE_DIR="$PWD/db/plants"
mkdir -p "$BASE_DIR"

CONTAINER_DIR="$PWD/db/containers"
mkdir -p "$CONTAINER_DIR"
DATASETS_CONTAINER="$CONTAINER_DIR/ncbi-datasets-cli.sif"
DATASETS_IMAGE="docker://staphb/ncbi-datasets:latest"

export SINGULARITY_CACHEDIR="$PWD/db/.singularity/cache"
mkdir -p "$SINGULARITY_CACHEDIR"

if [ ! -f "$DATASETS_CONTAINER" ]; then
    echo "Downloading NCBI Datasets container..."
    singularity pull "$DATASETS_CONTAINER" "$DATASETS_IMAGE"
fi
datasets_exec="singularity exec $DATASETS_CONTAINER datasets"

# -----------------------------
# 1. Download assembly_summary.txt
# -----------------------------
ASSEMBLY_FILE="$BASE_DIR/assembly_summary.txt"
echo "Downloading Plant assembly_summary.txt..."
if ! wget -O "$ASSEMBLY_FILE" https://ftp.ncbi.nlm.nih.gov/genomes/refseq/plant/assembly_summary.txt; then
    echo "❌ Download failed. Exiting."
    exit 1
fi

# -----------------------------
# 2. Extract reference genomes only
# -----------------------------
OUTPUT_CSV="$BASE_DIR/plant_reference_genome_${DATE}.csv"
awk -F "\t" '$0 !~ /^#/ && $5=="reference genome" {print $1","$2","$3","$5","$8}' "$ASSEMBLY_FILE" \
    > "$OUTPUT_CSV"

LINES=$(wc -l < "$OUTPUT_CSV")
if [ "$LINES" -eq 0 ]; then
    echo "No reference plant genomes found. Exiting."
    exit 1
fi
echo "✅ Extracted $LINES reference plant genomes into $OUTPUT_CSV"

# -----------------------------
# 3. Split CSV into chunks of 5000
# -----------------------------
split -l 5000 -d --additional-suffix=".csv" "$OUTPUT_CSV" "$BASE_DIR/temp_part_"
n=1
for f in "$BASE_DIR"/temp_part_*.csv; do
    mv "$f" "$BASE_DIR/plant_reference_genome_part${n}_${DATE}.csv"
    ((n++))
done
echo "✅ CSV split into $(ls "$BASE_DIR"/plant_reference_genome_part*_${DATE}.csv | wc -l) chunks"

# -----------------------------
# 4. Download genomes from CSV
# -----------------------------
for metadata in "$BASE_DIR"/plant_reference_genome_part*_${DATE}.csv; do
    echo "======================================"
    echo "Processing CSV: $metadata"
    echo "======================================"

    total_lines=$(wc -l < "$metadata")
    counter=0

    while IFS=, read -r accession rest; do
        [ -z "$accession" ] && continue
        counter=$((counter + 1))
        echo "[Progress] $counter/$total_lines genomes downloaded for this CSV"

        # Skip if genome already exists
        if ls "$BASE_DIR/"*"$accession"*.fna "$BASE_DIR/"*"$accession"*.fa "$BASE_DIR/"*"$accession"*.fasta 1> /dev/null 2>&1; then
            echo "Skipping $accession (already downloaded)"
            continue
        fi

        ZIP_FILE="$BASE_DIR/${accession}.zip"
        echo "Downloading $accession..."
        if ! $datasets_exec download genome accession "$accession" --filename "$ZIP_FILE"; then
            echo "❌ Error downloading $accession, skipping..."
            continue
        fi

        echo "Extracting $ZIP_FILE..."
        if ! unzip -o "$ZIP_FILE" -d "$BASE_DIR"; then
            echo "❌ Error extracting $ZIP_FILE, skipping..."
            rm -f "$ZIP_FILE"
            continue
        fi

        # Move genome files to BASE_DIR
        NESTED_DIR="$BASE_DIR/ncbi_dataset/data/$accession"
        if [ -d "$NESTED_DIR" ]; then
            find "$NESTED_DIR" -type f \( -iname "*.fna" -o -iname "*.fa" -o -iname "*.fasta" \) -exec mv {} "$BASE_DIR/" \;
        fi

        # Cleanup
        rm -rf "$ZIP_FILE" "$BASE_DIR/ncbi_dataset" *.md 2>/dev/null

        echo "✅ Download completed: $accession"
    done < "$metadata"

    echo "Finished processing $metadata"
done

echo "✅ All Plant reference genomes are now in $BASE_DIR"
echo "Containers are in $CONTAINER_DIR"

