#!/bin/bash --login
# ======================================
# Fungal Reference Genome Downloader (RESUME mode)
# ======================================

DATE=$(date +%F)  # YYYY-MM-DD format

# -----------------------------
# 0. Setup output directories
# -----------------------------
BASE_DIR="$PWD"
GROUP_DIR="$BASE_DIR/db/fungi"
CONTAINER_DIR="$BASE_DIR/db/containers"
LOG_FILE="$BASE_DIR/master_log_${DATE}.txt"

mkdir -p "$GROUP_DIR" "$CONTAINER_DIR"

# -----------------------------
# 1. Download the assembly summary
# -----------------------------
ASSEMBLY_FILE="$GROUP_DIR/assembly_summary.txt"
echo "[$(date)] Downloading assembly_summary.txt..." | tee -a "$LOG_FILE"
if wget -q -O "$ASSEMBLY_FILE" https://ftp.ncbi.nlm.nih.gov/genomes/refseq/fungi/assembly_summary.txt; then
    echo "✅ Download successful." | tee -a "$LOG_FILE"
else
    echo "❌ Download failed. Exiting." | tee -a "$LOG_FILE"
    exit 1
fi

# -----------------------------
# 2. Extract columns for reference genomes only (skip header)
# -----------------------------
OUTPUT_CSV="$GROUP_DIR/fungal_reference_genome_${DATE}.csv"
echo "Filtering reference genomes and extracting columns..." | tee -a "$LOG_FILE"

awk -F "\t" '$0 !~ /^#/ && $5=="reference genome" {print $1","$2","$3","$5","$8}' "$ASSEMBLY_FILE" > "$OUTPUT_CSV"

LINES=$(wc -l < "$OUTPUT_CSV")
if [ "$LINES" -eq 0 ]; then
    echo "No reference genomes found. Exiting." | tee -a "$LOG_FILE"
    exit 1
fi
echo "Extracted $LINES reference genomes into $OUTPUT_CSV" | tee -a "$LOG_FILE"

# -----------------------------
# 3. Split CSV into chunks of 5000 genomes
# -----------------------------
echo "Splitting CSV into 5000-line chunks..." | tee -a "$LOG_FILE"
cd "$GROUP_DIR"
split -l 5000 -d --additional-suffix=".csv" "$(basename "$OUTPUT_CSV")" temp_part_

n=1
for f in temp_part_*.csv; do
    mv "$f" "fungal_reference_genome_part${n}_${DATE}.csv"
    ((n++))
done

NUM_PARTS=$(ls fungal_reference_genome_part*_${DATE}.csv | wc -l)
echo "Done! Generated ${NUM_PARTS} files." | tee -a "$LOG_FILE"

# -----------------------------
# 4. Singularity + NCBI Datasets setup
# -----------------------------
DATASETS_CONTAINER="$CONTAINER_DIR/ncbi-datasets-cli.sif"
DATASETS_IMAGE="docker://staphb/ncbi-datasets:latest"

if [ ! -f "$DATASETS_CONTAINER" ]; then
    echo "Downloading NCBI Datasets container..." | tee -a "$LOG_FILE"
    singularity pull "$DATASETS_CONTAINER" "$DATASETS_IMAGE"
fi

datasets_exec="singularity exec $DATASETS_CONTAINER datasets"

# -----------------------------
# 5. Process split CSV files
# -----------------------------
for metadata in fungal_reference_genome_part*_${DATE}.csv; do
    echo "======================================" | tee -a "$LOG_FILE"
    echo " Processing CSV file: ${metadata}" | tee -a "$LOG_FILE"
    echo "======================================" | tee -a "$LOG_FILE"

    while IFS=, read -r accession rest; do
        [ -z "$accession" ] && continue

        # Skip if already downloaded
        if ls "$GROUP_DIR/${accession}"*.fna 1> /dev/null 2>&1; then
            echo "Skipping ${accession} (already downloaded)" | tee -a "$LOG_FILE"
            continue
        fi

        echo "Downloading: ${accession}" | tee -a "$LOG_FILE"
        zip_file="$GROUP_DIR/${accession}.zip"

        if ! $datasets_exec download genome accession "${accession}" --filename "$zip_file"; then
            echo "Error downloading ${accession}" | tee -a "$LOG_FILE"
            continue
        fi

        echo "Extracting ${accession}.zip" | tee -a "$LOG_FILE"
        if ! unzip -qo "$zip_file" -d "$GROUP_DIR"; then
            echo "Error extracting ${accession}.zip" | tee -a "$LOG_FILE"
            rm -f "$zip_file"
            continue
        fi

        # Move .fna files from extracted dataset to group dir
        find "$GROUP_DIR/ncbi_dataset" -name "*.fna" -exec mv {} "$GROUP_DIR/" \;

        # Cleanup
        rm -rf "$zip_file" "$GROUP_DIR/ncbi_dataset" *.md 2>/dev/null

        echo "✅ Completed: ${accession}" | tee -a "$LOG_FILE"
        echo ""
    done < "$metadata"

    echo "Finished processing ${metadata}" | tee -a "$LOG_FILE"
    echo ""
done

# -----------------------------
# 6. Summary
# -----------------------------
TOTAL_FASTA=$(find "$GROUP_DIR" -maxdepth 1 -name "*.fna" | wc -l)
echo "[$(date)] ✅ Fungal download completed: $TOTAL_FASTA genomes." | tee -a "$LOG_FILE"
echo "All data saved in: $GROUP_DIR" | tee -a "$LOG_FILE"
