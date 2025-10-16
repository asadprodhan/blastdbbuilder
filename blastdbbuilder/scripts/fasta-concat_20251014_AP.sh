#!/bin/bash

# ===========================
# Fasta Concatenation with Resume (No Renaming)
# ===========================

OUTDIR="$PWD"
COMBINED_FASTA="$OUTDIR/combined_concat_fasta.fna"
CHECKPOINT="$OUTDIR/checkpoint.log"

mkdir -p "$OUTDIR"

# -------------------------
# Step 1: Determine resume point
# -------------------------
resume_file_index=1
global_seq_counter=0

if [[ -f "$COMBINED_FASTA" && -s "$COMBINED_FASTA" ]] && [[ -f "$CHECKPOINT" && -s "$CHECKPOINT" ]]; then
    echo "[Resume] Existing FASTA and checkpoint found. Resuming..."
    read resume_file_index _ last_file <<< $(tail -n1 "$CHECKPOINT")
    echo "[Resume] Resuming from file index: $resume_file_index"
else
    echo "[Init] Starting fresh run"
    > "$COMBINED_FASTA"
    > "$CHECKPOINT"
    resume_file_index=1
fi

# -------------------------
# Step 2: Process files (append)
# -------------------------
total_files=$(ls -1 *.fna 2>/dev/null | wc -l)
if (( total_files == 0 )); then
    echo "[Error] No .fna files found in current directory."
    exit 1
fi

file_index=0
for fasta in *.fna; do
    file_index=$((file_index+1))
    if (( file_index < resume_file_index )); then
        continue
    fi

    echo "[Processing] $fasta ..."
    cat "$fasta" >> "$COMBINED_FASTA"

    # Update checkpoint
    echo "$((file_index+1)) 1 $fasta" > "$CHECKPOINT"

    percent=$(awk -v f="$file_index" -v t="$total_files" 'BEGIN {printf "%.2f", (f/t)*100}')
    echo "[Progress] Processed $file_index / $total_files files (${percent}%)"
done

echo "[Done] Combined FASTA written to $COMBINED_FASTA"
echo "[Done] Total files processed: $total_files"

# -------------------------
# Step 3: Integrity check
# -------------------------
actual=$(grep -c "^>" "$COMBINED_FASTA")
echo "[Integrity] Combined FASTA contains $actual sequences."
