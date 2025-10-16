#!/bin/bash --login
set -euo pipefail

OUTPUT_DIR="${1:-$PWD}"
ARCHAEA_DIR="$OUTPUT_DIR/db/archaea"
mkdir -p "$ARCHAEA_DIR"

# Containers centralized
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

# Download assembly_summary
wget -O "$ASSEMBLY_SUMMARY" https://ftp.ncbi.nlm.nih.gov/genomes/refseq/archaea/assembly_summary.txt

# Extract reference genomes into CSV
OUTPUT_CSV="$ARCHAEA_DIR/archaeal_reference_genome_${DATE}.csv"
awk -F "\t" '$0 !~ /^#/ && $5=="reference genome" {print $1","$2","$3","$5","$8}' "$ASSEMBLY_SUMMARY" \
    > "$OUTPUT_CSV"

# Split CSV
split -l 5000 -d --additional-suffix=".csv" "$OUTPUT_CSV" "$ARCHAEA_DIR/temp_part_"
n=1
for f in "$ARCHAEA_DIR"/temp_part_*.csv; do
    mv "$f" "$ARCHAEA_DIR/archaeal_reference_genome_part${n}_${DATE}.csv"
    ((n++))
done

# Process CSV sequentially
for metadata in "$ARCHAEA_DIR"/archaeal_reference_genome_part*_${DATE}.csv; do
    while IFS=, read -r accession rest; do
        [ -z "$accession" ] && continue

        ZIP_FILE="$ARCHAEA_DIR/${accession}.zip"
        echo "Downloading $accession..."
        $datasets_exec download genome accession "$accession" --filename "$ZIP_FILE"

        echo "Extracting $ZIP_FILE into $ARCHAEA_DIR"
        unzip -o "$ZIP_FILE" -d "$ARCHAEA_DIR"

        # Move all .fna to ARCHAEA_DIR
        find "$ARCHAEA_DIR/ncbi_dataset/data/$accession" -name "*.fna" -exec mv {} "$ARCHAEA_DIR/" \;

        # Clean up
        rm -rf "$ARCHAEA_DIR/ncbi_dataset"
        rm -f "$ZIP_FILE"
        rm -f "$ARCHAEA_DIR"/*.md 2>/dev/null
    done < "$metadata"
done

echo "✅ All Archaea genomes are now in $ARCHAEA_DIR"
echo "Containers are in $CONTAINER_DIR"
