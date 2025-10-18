#!/usr/bin/env bash
set -euo pipefail

# ================================================================
# Building a Large Customised Blastn Database
# Fully integrated with blastdbbuilder CLI
# Author: Asad Prodhan
# Date: 2025-10-18
# ================================================================

# -----------------------------
# Project root and directories
# -----------------------------
PROJECT_ROOT="$PWD"
SUMMARY_LOG="$PROJECT_ROOT/summary.log"

# -----------------------------
# Banner
# -----------------------------
echo "
🧬 B L A S T D B   B U I L D E R
Building a Customised Blastn Database
Project root: $PROJECT_ROOT
=======================================
" | tee -a "$SUMMARY_LOG"

# Container storage directory
CONTAINER_DIR="$PROJECT_ROOT/db/containers"
mkdir -p "$CONTAINER_DIR"

# Singularity cache directory
export SINGULARITY_CACHEDIR="$PROJECT_ROOT/db/.singularity/cache"
mkdir -p "$SINGULARITY_CACHEDIR"

# -----------------------------
# Default settings
# -----------------------------
CHUNK_SIZE_B=3000000000          # 3G bases in bytes
OUTPUT_DIR="$PROJECT_ROOT/blastnDB"
DB_BASENAME="nt"
COMPRESS_CHUNKS=false            # optional compression

# -----------------------------
# Container definitions
# -----------------------------
SEQKIT_CONTAINER="$CONTAINER_DIR/seqkit_2.10.1.sif"
SEQKIT_IMAGE="docker://quay.io/biocontainers/seqkit:2.10.1--he881be0_0"

BLAST_CONTAINER="$CONTAINER_DIR/ncbi-blast_2.16.0.sif"
BLAST_IMAGE="docker://quay.io/biocontainers/blast:2.16.0--h6f7f691_0"

# -----------------------------
# Pull containers if not already available
# -----------------------------
if [ ! -f "$SEQKIT_CONTAINER" ]; then
    echo "[$(date)] Downloading SeqKit container..." | tee -a "$SUMMARY_LOG"
    singularity pull "$SEQKIT_CONTAINER" "$SEQKIT_IMAGE"
else
    echo "[$(date)] SeqKit container already exists." | tee -a "$SUMMARY_LOG"
fi

if [ ! -f "$BLAST_CONTAINER" ]; then
    echo "[$(date)] Downloading BLAST+ container..." | tee -a "$SUMMARY_LOG"
    singularity pull "$BLAST_CONTAINER" "$BLAST_IMAGE"
else
    echo "[$(date)] BLAST+ container already exists." | tee -a "$SUMMARY_LOG"
fi

# -----------------------------
# Executable shortcuts
# -----------------------------
seqkit_exec="singularity exec $SEQKIT_CONTAINER seqkit"
blast_exec="singularity exec $BLAST_CONTAINER blastn"

# -----------------------------
# Prepare output directories
# -----------------------------
mkdir -p "$OUTPUT_DIR"
CHUNK_TMP="$OUTPUT_DIR/tmp_chunks"
LOG_DIR="$OUTPUT_DIR/logs"
mkdir -p "$CHUNK_TMP" "$LOG_DIR"

# -----------------------------
# Detect concatenated FASTA file
# -----------------------------
COMBINED_FASTA=$(find "$PROJECT_ROOT" -maxdepth 1 -type f \( -iname "*.fna" -o -iname "*.fa" -o -iname "*.fasta" \) | head -n 1)

if [ -z "$COMBINED_FASTA" ]; then
    echo "❌ ERROR: No concatenated FASTA found in project root ($PROJECT_ROOT)" | tee -a "$SUMMARY_LOG"
    exit 1
else
    echo "✅ Using concatenated FASTA: $COMBINED_FASTA" | tee -a "$SUMMARY_LOG"
fi

# -----------------------------
# Split FASTA into chunks
# -----------------------------
echo "➡️ Splitting FASTA into ~$(($CHUNK_SIZE_B/1000000)) MB chunks..." | tee -a "$SUMMARY_LOG"

singularity exec "$SEQKIT_CONTAINER" seqkit split2 \
    --by-size "$CHUNK_SIZE_B" \
    -O "$CHUNK_TMP" \
    --force \
    "$COMBINED_FASTA" \
    -j 4

CHUNKS=("$CHUNK_TMP"/*.fasta)
echo "✅ Total chunks created: ${#CHUNKS[@]}" | tee -a "$SUMMARY_LOG"

# -----------------------------
# Build BLAST DBs for each chunk
# -----------------------------
echo "➡️ Building BLAST databases for each chunk..." | tee -a "$SUMMARY_LOG"
DB_LIST=()

for CHUNK_FILE in "${CHUNKS[@]}"; do
    BASENAME=$(basename "$CHUNK_FILE" .fasta)
    DB_PREFIX="$OUTPUT_DIR/$BASENAME"
    DB_LIST+=("$DB_PREFIX")
    CHUNK_LOG="$LOG_DIR/$BASENAME.log"

    # Skip existing DBs for resume capability
    if [ -f "$DB_PREFIX.nhr" ]; then
        echo "⏩ Skipping (already built): $BASENAME" | tee -a "$SUMMARY_LOG"
        continue
    fi

    echo "🔹 Building DB for: $BASENAME" | tee -a "$SUMMARY_LOG"
    singularity exec "$BLAST_CONTAINER" makeblastdb \
        -in "$CHUNK_FILE" \
        -dbtype nucl \
        -blastdb_version 5 \
        -max_file_sz "${CHUNK_SIZE_B}B" \
        -out "$DB_PREFIX" \
        -title "$BASENAME" \
        -logfile "$CHUNK_LOG" \
        -hash_index

    echo "✅ DB built for $BASENAME" | tee -a "$SUMMARY_LOG"
    rm -f "$CHUNK_FILE"  # optionally remove chunk to save space
done

# -----------------------------
# Verify all chunk databases
# -----------------------------
echo "➡️ Verifying all BLAST DB chunks..." | tee -a "$SUMMARY_LOG"
for DB in "${DB_LIST[@]}"; do
    if [ ! -f "$DB.nhr" ] || [ ! -f "$DB.nin" ] || [ ! -f "$DB.nsq" ]; then
        echo "❌ Missing files for $DB. Aborting." | tee -a "$SUMMARY_LOG"
        exit 1
    fi
done
echo "✅ All chunks verified successfully." | tee -a "$SUMMARY_LOG"

# -----------------------------
# Create combined alias database
# -----------------------------
ALIAS_FILE="$OUTPUT_DIR/$DB_BASENAME"
DBLIST_FILE=$(mktemp)
for DB in "${DB_LIST[@]}"; do
    REL_PATH=$(realpath --relative-to="$OUTPUT_DIR" "$DB")
    echo "$REL_PATH" >> "$DBLIST_FILE"
done

echo "➡️ Creating combined alias database..." | tee -a "$SUMMARY_LOG"
singularity exec "$BLAST_CONTAINER" blastdb_aliastool \
    -title "$DB_BASENAME" \
    -dblist_file "$DBLIST_FILE" \
    -out "$ALIAS_FILE" \
    -dbtype nucl
rm "$DBLIST_FILE"

echo "✅ Alias database created: $ALIAS_FILE" | tee -a "$SUMMARY_LOG"

# -----------------------------
# Final summary
# -----------------------------
DATE_STR=$(date +%F)
TOTAL_SEQS=$(singularity exec "$SEQKIT_CONTAINER" seqkit stats "$COMBINED_FASTA" -T | awk 'NR==2{print $2}')
{
    echo ""
    echo "BLAST DB build summary ($DATE_STR)"
    echo "---------------------------------------"
    echo "FASTA: $COMBINED_FASTA"
    echo "Total sequences: $TOTAL_SEQS"
    echo "Chunks processed: ${#CHUNKS[@]}"
    echo "DB basename: $DB_BASENAME"
    echo "Output dir: $OUTPUT_DIR"
    echo "---------------------------------------"
} >> "$SUMMARY_LOG"

echo "🎯 BLAST DB build complete!"
echo "Master summary log: $SUMMARY_LOG"
