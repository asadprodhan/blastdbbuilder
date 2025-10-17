#!/bin/bash --login
set -euo pipefail

# ======================================
# Archaeal Reference Genome Downloader (Resume + Structured)
# ======================================

OUTPUT_DIR="${1:-$PWD}"
ARCHAEA_DIR="$OUTPUT_DIR/db/archaea"
mkdir -p "$ARCHAEA_DIR"

# -----------------------------
# Containers centralized
# -----------------------------
CONTAINER_DIR="$OUTPUT_DIR/db/containers"
mkdir -p "$CONTAINER_DIR"
DATASETS_CONTAINER="$CONTAINER_DIR/ncbi-datasets-cli.sif"
DATASETS_IMAGE="docker://staphb/ncbi-datasets:latest"

export SINGULARITY_CACHEDIR="$OUTPUT_DIR/db/.singularity/cache"
mkdir -p "$SINGULARITY_CACHEDIR"

if [ ! -f "$DATASETS_CONTAINER" ]; then
    echo "Downloading NCBI Datasets container..."
    singularity pull "$DATASETS_CONTAINER" "$DATASETS_IMAGE"
fi
datasets_exec="singularity exec $DATASETS_CONTAINER datasets"

DATE=$(date +%F)
ASSEMBLY_SUMMARY="$ARCHAEA_DIR/assembly_summary.txt"

# -----------------------------
# 1. Download assembly_summary
# -----------------------------
echo "Downloading assembly_summary.txt for Archaea..."
if wget -O "$ASSEMBLY_SUMMARY" https://ftp.ncbi.nlm.nih.gov/genomes/refseq/archaea/assembly_summary.txt; then
    echo "✅ Assembly summary downloaded successfully."
else
    echo "❌ Failed to download assembly_summary.txt. Exiting."
    exit 1
fi

# -----------------------------
# 2. Extract reference genomes into CSV
# -----------------------------
OUTPUT_CSV="$ARCHAEA_DIR/archaeal_reference_genome_${DATE}.csv"
echo "Filtering reference genomes and creating CSV..."
awk -F "\t" '$0 !~ /^#/ && $5=="reference genome" {print $1","$2","$3","$5","$8}' "$ASSEMBLY_SUMMARY" \
    > "$OUTPUT_CSV"

LINES=$(wc -l < "$OUTPUT_CSV")
if [ "$LINES" -eq 0 ]; then
    echo "No reference genomes found. Exiting."
    exit 1
fi
echo "Extracted $LINES reference genomes into $OUTPUT_CSV"

# -----------------------------
# 3. Split CSV into chunks of 5000 genomes
# -----------------------------
echo "Splitting CSV into 5000-line chunks..."
split -l 5000 -d --additional-suffix=".csv" "$OUTPUT_CSV" "$ARCHAEA_DIR/temp_part_"
n=1
for f in "$ARCHAEA_DIR"/temp_part_*.csv; do
    mv "$f" "$ARCHAEA_DIR/archaeal_reference_genome_part${n}_${DATE}.csv"
    ((n++))
done
echo "Done! Generated $(ls "$ARCHAEA_DIR"/archaeal_reference_genome_part*_${DATE}.csv | wc -l) files."

# -----------------------------
# 4. Process each CSV sequentially
# -----------------------------
for metadata in "$ARCHAEA_DIR"/archaeal_reference_genome_part*_${DATE}.csv; do
    echo "======================================"
    echo " Processing CSV file: ${metadata}"
    echo "======================================"

    while IFS=, read -r accession rest; do
        [ -z "$accession" ] && continue

        ZIP_FILE="$ARCHAEA_DIR/${accession}.zip"

        # Skip if genome already downloaded
        if ls "$ARCHAEA_DIR/${accession}"*.fna 1> /dev/null 2>&1; then
            echo "Skipping ${accession} (already downloaded)"
            continue
        fi

        echo "Downloading ${accession}..."
        if ! $datasets_exec download genome accession "$accession" --filename "$ZIP_FILE"; then
            echo "Error downloading ${accession}"
            continue
        fi

        echo "Extracting ${accession}.zip..."
        if ! unzip -o "$ZIP_FILE" -d "$ARCHAEA_DIR"; then
            echo "Error extracting ${ZIP_FILE}"
            rm -f "$ZIP_FILE"
            continue
        fi

        # Move all .fna files to ARCHAEA_DIR
        find "$ARCHAEA_DIR/ncbi_dataset/data/$accession" -name "*.fna" -exec mv {} "$ARCHAEA_DIR/" \;

        # Clean up
        rm -rf "$ARCHAEA_DIR/ncbi_dataset"
        rm -f "$ZIP_FILE"
        rm -f "$ARCHAEA_DIR"/*.md 2>/dev/null

        echo "✅ Download completed: ${accession}"
        echo ""
    done < "$metadata"

    echo "Finished processing ${metadata}"
    echo ""
done

echo "✅ All Archaeal genomes are now in $ARCHAEA_DIR"
echo "Containers are in $CONTAINER_DIR"
