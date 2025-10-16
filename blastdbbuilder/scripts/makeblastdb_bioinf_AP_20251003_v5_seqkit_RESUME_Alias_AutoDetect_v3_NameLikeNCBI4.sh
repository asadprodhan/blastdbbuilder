#!/bin/bash
# ================================================================
# Building a Large Customised Blastn Database
# Author: Asad Prodhan
# Date: 2025-10-15
# Description: Safe, resume-capable, chunked BLAST DB build
# ================================================================

set -euo pipefail

# -----------------------------
# Banner
# -----------------------------
echo "
🧬 B L A S T D B   B U I L D E R
Building a Large Customised Blastn Database
Asad Prodhan PhD
=======================================
"

# -----------------------------
# Default settings (can be overridden by flags)
# -----------------------------
CHUNK_SIZE_B=3000000000          # 3G bases in bytes
OUTPUT_DIR="$PWD/blastnDB"
DB_BASENAME="nt"
SEQKIT_CONTAINER="$PWD/containers/seqkit_2.10.1.sif"
BLAST_CONTAINER="$PWD/containers/ncbi-blast_2.16.0.sif"
COMPRESS_CHUNKS=false           # compression disabled

# -----------------------------
# Usage function
# -----------------------------
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -c, --chunk-size   <size>      Chunk size in bytes (default: 3000000000 for 3G)"
    echo "  -o, --output-dir   <dir>       Output directory (default: $PWD/blastnDB)"
    echo "  -b, --db-basename  <name>      Base name for DB and alias (default: nt)"
    echo "  --seqkit           <path>      Path to SeqKit Singularity container"
    echo "  --blast            <path>      Path to BLAST+ Singularity container"
    echo "  -h, --help                     Show this help message"
    echo ""
    exit 1
}

# -----------------------------
# Parse command line arguments
# -----------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        -c|--chunk-size)
            CHUNK_SIZE_B="$2"
            shift 2
            ;;
        -o|--output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -b|--db-basename)
            DB_BASENAME="$2"
            shift 2
            ;;
        --seqkit)
            SEQKIT_CONTAINER="$2"
            shift 2
            ;;
        --blast)
            BLAST_CONTAINER="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "❌ Unknown option: $1"
            usage
            ;;
    esac
done

# -----------------------------
# Step 0 — Setup directories and log
# -----------------------------
CHUNK_TMP="$OUTPUT_DIR/tmp_chunks"
LOG_DIR="$OUTPUT_DIR/logs"
mkdir -p "$OUTPUT_DIR" "$CHUNK_TMP" "$LOG_DIR"

LOGFILE="${LOG_DIR}/makeblastdb_pipeline_$(date +%Y%m%d_%H%M%S).log"

echo "🧬 Starting BLAST DB pipeline" | tee -a "$LOGFILE"
echo "Output directory: $OUTPUT_DIR" | tee -a "$LOGFILE"
echo "Temp chunk directory: $CHUNK_TMP" | tee -a "$LOGFILE"
echo "Logs directory: $LOG_DIR" | tee -a "$LOGFILE"
echo "SeqKit container: $SEQKIT_CONTAINER" | tee -a "$LOGFILE"
echo "BLAST container: $BLAST_CONTAINER" | tee -a "$LOGFILE"
echo "Pipeline log: $LOGFILE" | tee -a "$LOGFILE"
echo "Chunk size (bytes): $CHUNK_SIZE_B" | tee -a "$LOGFILE"
echo "---------------------------------------------" | tee -a "$LOGFILE"

# -----------------------------
# Step 1 — Auto-detect input FASTA
# -----------------------------
INPUT_FASTA=$(find "$PWD" -maxdepth 1 -type f \( -iname "*combined*.fasta" -o -iname "*combined*.fna" -o -iname "*combined*.fa" \) | head -n 1)
if [ -z "$INPUT_FASTA" ]; then
    echo "❌ ERROR: No input FASTA file found with 'combined' in the name (*.fasta, *.fna, *.fa)" | tee -a "$LOGFILE"
    exit 1
else
    echo "✅ Auto-detected input FASTA: $INPUT_FASTA" | tee -a "$LOGFILE"
fi

# -----------------------------
# Step 2 — Split FASTA safely with SeqKit if DB not yet exist
# -----------------------------
if ! ls "$OUTPUT_DIR"/nt.*.nhr &>/dev/null; then
    echo "➡️ Splitting FASTA safely with SeqKit by total bases..." | tee -a "$LOGFILE"
    singularity exec "$SEQKIT_CONTAINER" seqkit split2 \
        --by-length "$CHUNK_SIZE_B" \
        -O "$CHUNK_TMP" \
        --force \
        "$INPUT_FASTA" \
        2>&1 | tee -a "$LOGFILE"
else
    echo "⏩ BLAST DBs already exist. Skipping splitting." | tee -a "$LOGFILE"
fi

# -----------------------------
# Step 3 — Rename chunks to nt.XXX.fna format
# -----------------------------
CHUNKS=($CHUNK_TMP/*)
COUNT=1
CHUNKS_RENAMED=()
for CHUNK in "${CHUNKS[@]}"; do
    NEW_NAME=$(printf "%s/nt.%03d.fna" "$OUTPUT_DIR" "$COUNT")
    mv "$CHUNK" "$NEW_NAME"
    CHUNKS_RENAMED+=("$NEW_NAME")
    echo "  $CHUNK → $NEW_NAME" | tee -a "$LOGFILE"
    COUNT=$((COUNT+1))
done

CHUNKS=("${CHUNKS_RENAMED[@]}")
echo "✅ Created ${#CHUNKS[@]} chunks:" | tee -a "$LOGFILE"
printf '  %s\n' "${CHUNKS[@]}" | tee -a "$LOGFILE"
echo "---------------------------------------------" | tee -a "$LOGFILE"

# -----------------------------
# Step 4 — Build BLAST DB for each chunk (resume-capable)
# -----------------------------
echo "➡️ Building BLAST databases for each chunk..." | tee -a "$LOGFILE"
DB_LIST=()
for CHUNK_FILE in "${CHUNKS[@]}"; do
    BASENAME=$(basename "$CHUNK_FILE")
    BASENAME=${BASENAME%.fna*} # remove .fna
    DB_PREFIX="$OUTPUT_DIR/$BASENAME"
    DB_LIST+=("$DB_PREFIX")
    CHUNK_LOG="$LOG_DIR/$BASENAME.log"

    # Skip if DB already exists
    if [ -f "$DB_PREFIX.nhr" ] || [ -f "$DB_PREFIX.nin" ] || [ -f "$DB_PREFIX.nsq" ]; then
        echo "⏩ DB for $BASENAME already exists. Skipping..." | tee -a "$LOGFILE"
        continue
    fi

    echo "🔹 Building DB for: $BASENAME" | tee -a "$LOGFILE"
    echo "   Log: $CHUNK_LOG" | tee -a "$LOGFILE"

    singularity exec "$BLAST_CONTAINER" makeblastdb \
        -in "$CHUNK_FILE" \
        -dbtype nucl \
        -blastdb_version 5 \
        -max_file_sz "$CHUNK_SIZE_B"B \
        -out "$DB_PREFIX" \
        -title "$BASENAME" \
        -logfile "$CHUNK_LOG" \
        -hash_index

    if [ $? -eq 0 ]; then
        echo "✅ DB built for $BASENAME" | tee -a "$LOGFILE"
        # Delete the original chunk to save space
        rm -f "$CHUNK_FILE"
        echo "🗑️ Deleted original FASTA chunk: $CHUNK_FILE" | tee -a "$LOGFILE"
    else
        echo "❌ ERROR building DB for $BASENAME. Check $CHUNK_LOG" | tee -a "$LOGFILE"
    fi
done

# -----------------------------
# Step 5 — Integrity check
# -----------------------------
echo "➡️ Checking integrity of all chunk DBs..." | tee -a "$LOGFILE"
for DB in "${DB_LIST[@]}"; do
    if [ ! -f "$DB.nhr" ] || [ ! -f "$DB.nin" ] || [ ! -f "$DB.nsq" ]; then
        echo "❌ Missing files for $DB. Cannot create alias. Aborting." | tee -a "$LOGFILE"
        exit 1
    fi
done
echo "✅ All chunks have required BLAST DB files." | tee -a "$LOGFILE"

# -----------------------------
# Step 6 — Create portable alias database
# -----------------------------
ALIAS_FILE="$OUTPUT_DIR/$DB_BASENAME"   # no extension
DBLIST_FILE=$(mktemp)
for DB in "${DB_LIST[@]}"; do
    REL_PATH=$(realpath --relative-to="$OUTPUT_DIR" "$DB")
    echo "$REL_PATH" >> "$DBLIST_FILE"
done

echo "➡️ Creating combined alias database (portable)..." | tee -a "$LOGFILE"
singularity exec "$BLAST_CONTAINER" blastdb_aliastool \
    -title "$DB_BASENAME" \
    -dblist_file "$DBLIST_FILE" \
    -out "$ALIAS_FILE" \
    -dbtype nucl

rm "$DBLIST_FILE"
echo "✅ Alias created successfully: $ALIAS_FILE" | tee -a "$LOGFILE"
echo "---------------------------------------------" | tee -a "$LOGFILE"

# -----------------------------
# Step 7 — Summary usage
# -----------------------------
echo "🎯 All done! You can now run BLAST like this:"
echo "singularity exec \"$BLAST_CONTAINER\" \\"
echo "    blastn -db $ALIAS_FILE -query your_query.fna -out results.txt"
echo "📄 Detailed log saved to: $LOGFILE"
# -----------------------------
# Step 8 — Clean up intermediate files
# -----------------------------
echo "🧹 Cleaning up intermediate files..." | tee -a "$LOGFILE"
rm -fv "$PWD"/*.fna "$PWD"/*.fa "$PWD"/*.fasta 2>/dev/null
rm -rf "$CHUNK_TMP" 2>/dev/null
rm -rf "$PWD/containers" 2>/dev/null
echo "✅ Cleanup complete." | tee -a "$LOGFILE"
