#!/bin/bash --login

# -----------------------------
# Get current date
# -----------------------------
DATE=$(date +%F)  # YYYY-MM-DD format

# -----------------------------
# 1. Download the viral assembly summary
# -----------------------------
echo "Downloading assembly_summary.txt..."
if wget -O assembly_summary.txt https://ftp.ncbi.nlm.nih.gov/genomes/refseq/viral/assembly_summary.txt; then
    echo "Download successful."
else
    echo "Download failed. Exiting."
    exit 1
fi

# -----------------------------
# 2. Extract columns 1,2,3,5,8 from all assemblies, skip header
# -----------------------------

OUTPUT_CSV="viral_genomes_${DATE}.csv"
echo "Extracting columns 1,2,3,5,8 from all viral assemblies..."
awk -F "\t" '$0 !~ /^#/ {print $1","$2","$3","$5","$8}' assembly_summary.txt \
    > "$OUTPUT_CSV"

# $0 !~ /^#/ Only process lines that do NOT start with 

LINES=$(wc -l < "$OUTPUT_CSV")
if [ "$LINES" -eq 0 ]; then
    echo "No viral genomes found. Exiting."
    exit 1
fi
echo "Extracted $LINES viral genomes into $OUTPUT_CSV"

# -----------------------------
# 3. Split CSV into chunks of 5000 genomes with date-stamped filenames
# -----------------------------
echo "Splitting CSV into 5000-line chunks..."
split -l 5000 -d --additional-suffix=".csv" "$OUTPUT_CSV" temp_part_

# Rename sequentially with date
n=1
for f in temp_part_*.csv; do
    mv "$f" "viral_genomes_part${n}_${DATE}.csv"
    ((n++))
done

echo "Done! Generated $(ls viral_genomes_part*_*.csv | wc -l) chunk files."
# 
# -----------------------------
# -----------------------------
# 4. Singularity + NCBI Datasets setup
# -----------------------------
#
export SINGULARITY_CACHEDIR="$PWD/.singularity/cache"
mkdir -p "$SINGULARITY_CACHEDIR"

CONTAINER_DIR="$PWD/containers"
DATASETS_CONTAINER="$CONTAINER_DIR/ncbi-datasets-cli.sif"
DATASETS_IMAGE="docker://staphb/ncbi-datasets:latest"
mkdir -p "$CONTAINER_DIR"

if [ ! -f "$DATASETS_CONTAINER" ]; then
  echo "Downloading NCBI Datasets container..."
  singularity pull "$DATASETS_CONTAINER" "$DATASETS_IMAGE"
fi

datasets_exec="singularity exec $DATASETS_CONTAINER datasets"

# -----------------------------
# 5. Process split CSV files
# -----------------------------
for metadata in viral_genomes_part*_${DATE}.csv; do
    echo "======================================"
    echo " Processing CSV file: ${metadata}"
    echo "======================================"

    while IFS=, read -r accession rest; do
        [ -z "$accession" ] && continue

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
