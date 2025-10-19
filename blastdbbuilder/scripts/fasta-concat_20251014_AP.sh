#!/bin/bash
# =========================================
# Fasta Concatenation Script (CLI.py Consistent)
# Handles .fna, .fa, .fasta from all groups
# Updates master summary.log in project root
# Moves combined FASTA to project root and cleans up db/
# =========================================

PROJECT_ROOT="$PWD"
CONCAT_DIR="$PROJECT_ROOT/db/concat"
COMBINED_FASTA="$CONCAT_DIR/nt.fna"
CHECKPOINT="$CONCAT_DIR/checkpoint.log"
SUMMARY_LOG="$PROJECT_ROOT/summary.log"

# Create concat directory
mkdir -p "$CONCAT_DIR"

# Step 0: Move all genomes from groups into concat directory
echo "📂 Moving genomes from all groups into $CONCAT_DIR ..."
for group in archaea bacteria fungi virus plants; do
    GROUP_DIR="$PROJECT_ROOT/db/$group"
    if [ -d "$GROUP_DIR" ]; then
        shopt -s nullglob
        for file in "$GROUP_DIR"/*.{fna,fa,fasta}; do
            mv "$file" "$CONCAT_DIR/"
        done
        shopt -u nullglob
    fi
done

# Step 1: Initialize resume
resume_file_index=1
if [[ -f "$COMBINED_FASTA" && -s "$COMBINED_FASTA" ]] && [[ -f "$CHECKPOINT" && -s "$CHECKPOINT" ]]; then
    echo "[Resume] Existing combined FASTA and checkpoint found."
    read resume_file_index _ last_file <<< $(tail -n1 "$CHECKPOINT")
    echo "[Resume] Resuming from file index: $resume_file_index"
else
    echo "[Init] Starting fresh concatenation run"
    > "$COMBINED_FASTA"
    > "$CHECKPOINT"
fi

# Step 2: Count total files to process
shopt -s nullglob
ALL_FILES=("$CONCAT_DIR"/*.{fna,fa,fasta})
TOTAL_FILES=${#ALL_FILES[@]}
shopt -u nullglob

if (( TOTAL_FILES == 0 )); then
    echo "[Error] No genome files found in $CONCAT_DIR"
    exit 1
fi

echo "🔢 Total genome files to concatenate: $TOTAL_FILES"

# Step 3: Concatenate with progress reporting
file_index=0
for fasta in "${ALL_FILES[@]}"; do
    file_index=$((file_index+1))
    if (( file_index < resume_file_index )); then
        continue
    fi

    echo "[Processing] $fasta ..."
    cat "$fasta" >> "$COMBINED_FASTA"

    # Update checkpoint
    echo "$((file_index+1)) 1 $fasta" > "$CHECKPOINT"

    percent=$(awk -v f="$file_index" -v t="$TOTAL_FILES" 'BEGIN {printf "%.2f", (f/t)*100}')
    echo "[Progress] Processed $file_index / $TOTAL_FILES files (${percent}%)"
done

# Step 4: Integrity check
SEQ_COUNT=$(grep -c "^>" "$COMBINED_FASTA")
echo "[Integrity] Combined FASTA contains $SEQ_COUNT sequences"

# Step 5: Update master summary.log
{
    echo "===== Concatenation Summary ====="
    echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Combined FASTA (before moving): $COMBINED_FASTA"
    echo "Total genome files concatenated: $TOTAL_FILES"
    echo "Total sequences in combined FASTA: $SEQ_COUNT"
    echo "================================="
} >> "$SUMMARY_LOG"

# Step 6: Move combined FASTA two levels up
TARGET_FASTA="$PROJECT_ROOT/../../nt.fna"
mv "$COMBINED_FASTA" "$TARGET_FASTA"
echo "📂 Moved concatenated FASTA to $TARGET_FASTA"

echo "✅ Concatenation completed. Master summary.log updated at $SUMMARY_LOG"
