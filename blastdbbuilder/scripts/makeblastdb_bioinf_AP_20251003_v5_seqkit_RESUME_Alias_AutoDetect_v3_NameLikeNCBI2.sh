#!/bin/bash
# ================================================================
# Building a Large Customised Blastn Database
# Fully integrated with blastdbbuilder CLI
# Author: Asad Prodhan
# Date: 2025-10-17
# ================================================================

set -euo pipefail

# -----------------------------
# Project root
# -----------------------------
PROJECT_ROOT="$PWD"
SUMMARY_LOG="$PROJECT_ROOT/summary.log"

# -----------------------------
# Default settings (can override via flags)
# -----------------------------
CHUNK_SIZE_B=3000000000          # 3G bases in bytes
OUTPUT_DIR="$PROJECT_ROOT/blastnDB"
DB_BASENAME="nt"
SEQKIT_CONTAINER="$PROJECT_ROOT/containers/seqkit_2.10.1.sif"
BLAST_CONTAINER="$PROJECT_ROOT/containers/ncbi-blast_2.16.0.sif"
COMPRESS_CHUNKS=false            # optional compression

# -----------------------------
# Setup directories
# -----------------------------
CHUNK_TMP="$OUTPUT_DIR/tmp_chunks"
LOG_DIR="$OUTPUT_DIR/logs"
mkdir -p "$OUTPUT_DIR" "$CHUNK_TMP" "$LOG_DIR"
mkdir -p "$PROJECT_ROOT/containers"

# -----------------------------
# Banner
# -----------------------------
echo "
🧬 B L A S T D B   B U I L D E R
Building a Large Customised Blastn Database
Project root: $PROJECT_ROOT
=======================================
" | tee -a "$SUMMARY_LOG"

# -----------------------------
# Step 0 — Detect concatenated FASTA
# -----------------------------
COMBINED_FASTA=$(find "$PROJECT_ROOT" -maxdepth 1 -type f \( -iname "*.fna" -o -iname "*.fa" -o -iname "*.fasta" \) | head -n 1)

if [ -z "$COMBINED_FASTA" ]; then
    echo "❌ ERROR: No concatenated FASTA found in project root ($PROJECT_ROOT)" | tee -a "$SUMMARY_LOG"
    exit 1
else
    echo "✅ Using concatenated FASTA: $COMBINED_FASTA" | tee -a "$SUMMARY_LOG"
fi

# -----------------------------
# Step 1 — Setup containers
# -----------------------------
if [ ! -f "$SEQKIT_CONTAINER" ]; then
    echo "Downloading SeqKit container..." | tee -a "$SUMMARY_LOG"
    singularity pull "$SEQKIT_CONTAINER" "docker://shenwei356/seqkit:2.10.1"
fi

if [ ! -f "$BLAST_CONTAINER" ]; then
    echo "Downloading BLAST+ container..." | tee -a "$SUMMARY_LOG"
    singularity pull "$BLAST_CONTAINER" "docker://ncbi/blast:2.16.0"
fi

# -----------------------------
# Step 2 — Split concatenated FASTA into chunks
# -----------------------------
echo "➡️ Splitting FASTA into ~$(($CHUNK_SIZE_B/1000000)) MB chunks..." | tee -a "$SUMMARY_LOG"

CHUNKS=()
COUNT=1

for CHUNK_FILE in $(singularity exec "$SEQKIT_CONTAINER" seqkit split2 --by-length "$CHUNK_SIZE_B" -O "$CHUNK_TMP" --force "$COMBINED_FASTA" -j 4 | awk '{print $NF}'); do
    NEW_NAME=$(printf "%s/nt.%03d.fna" "$OUTPUT_DIR" "$COUNT")
    mv "$CHUNK_FILE" "$NEW_NAME"
    CHUNKS+=("$NEW_NAME")
    echo "  Chunk created: $NEW_NAME" | tee -a "$SUMMARY_LOG"
    COUNT=$((COUNT+1))
done

echo "✅ Total chunks created: ${#CHUNKS[@]}" | tee -a "$SUMMARY_LOG"

# -----------------------------
# Step 3 — Build BLAST DBs for each chunk (resume-capable)
# -----------------------------
echo "➡️ Building BLAST databases for each chunk..." | tee -a "$SUMMARY_LOG"
TOTAL_CHUNKS=${#CHUNKS[@]}
CURRENT_CHUNK=0
DB_LIST=()

for CHUNK_FILE in "${CHUNKS[@]}"; do
    CURRENT_CHUNK=$((CURRENT_CHUNK+1))
    BASENAME=$(basename "$CHUNK_FILE" .fna)
    DB_PREFIX="$OUTPUT_DIR/$BASENAME"
    DB_LIST+=("$DB_PREFIX")
    CHUNK_LOG="$LOG_DIR/$BASENAME.log"

    # Skip if DB exists
    if [ -f "$DB_PREFIX.nhr" ]; then
        echo "⏩ [$CURRENT_CHUNK/$TOTAL_CHUNKS] DB already exists: $BASENAME" | tee -a "$SUMMARY_LOG"
        continue
    fi

    echo "🔹 [$CURRENT_CHUNK/$TOTAL_CHUNKS] Building DB for: $BASENAME" | tee -a "$SUMMARY_LOG"
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

    # Optionally remove chunk to save space
    rm -f "$CHUNK_FILE"
done

# -----------------------------
# Step 4 — Verify all chunks
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
# Step 5 — Create combined alias database
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
# Step 6 — Update master summary.log
# -----------------------------
DATE_STR=$(date +%F)
TOTAL_SEQS=$(singularity exec "$SEQKIT_CONTAINER" seqkit stats "$COMBINED_FASTA" -T | awk 'NR==2{print $2}')
echo "" >> "$SUMMARY_LOG"
echo "BLAST DB build summary ($DATE_STR)" >> "$SUMMARY_LOG"
echo "---------------------------------------" >> "$SUMMARY_LOG"
echo "Concatenated FASTA: $COMBINED_FASTA" >> "$SUMMARY_LOG"
echo "Total sequences concatenated: $TOTAL_SEQS" >> "$SUMMARY_LOG"
echo "Chunks processed: ${#CHUNKS[@]}" >> "$SUMMARY_LOG"
echo "DB basename: $DB_BASENAME" >> "$SUMMARY_LOG"
echo "Database build completed at: $(date +'%Y-%m-%d %H:%M:%S')" >> "$SUMMARY_LOG"
echo "---------------------------------------" >> "$SUMMARY_LOG"

# -----------------------------
# Step 7 — Done
# -----------------------------
echo "🎯 BLAST DB build complete!" | tee -a "$SUMMARY_LOG"
echo "Master summary log updated at: $SUMMARY_LOG"
