#!/usr/bin/env python3
# blastdbbuilder/cli.py
# ======================================
# Automated genome download, concatenation, and BLAST DB builder
# ======================================

import argparse
import os
import sys
import subprocess
import datetime
import csv
import glob
import shutil

# -----------------------------
# Utility to run shell commands
# -----------------------------
def run_cmd(cmd, cwd=None):
    """Run a command and print stdout/stderr"""
    print("Running:", " ".join(cmd), flush=True)
    result = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print("[ERROR] Command failed:", " ".join(cmd), flush=True)
        print(result.stderr, flush=True)
        raise subprocess.CalledProcessError(result.returncode, cmd)
    return result.stdout

# -----------------------------
# Utility to write to master summary.log
# -----------------------------
def write_summary(summary_log, message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(summary_log, "a", encoding="utf-8", errors="replace") as f:
        f.write(f"[{timestamp}] {message}\n")

# -----------------------------
# Progress emitter (stdout + summary.log)
# -----------------------------
def emit_progress(summary_log, group_name, done, total, accession=None, status=None):
    parts = [f"[progress][{group_name}] {done}/{total}"]
    if accession:
        parts.append(accession)
    if status:
        parts.append(f"status={status}")
    msg = " ".join(parts)
    print(msg, flush=True)
    write_summary(summary_log, msg)

# -----------------------------
# Ensure container exists
# -----------------------------
def ensure_container(container_dir, container_name, image):
    container_path = os.path.join(container_dir, container_name)
    if not os.path.isfile(container_path):
        print(f"[FILE] Downloading container: {container_name}", flush=True)
        os.makedirs(container_dir, exist_ok=True)
        run_cmd(["singularity", "pull", container_path, image])
    return container_path



def _is_valid_assembly_summary(path: str) -> bool:
    """Lightweight sanity check so resume can trust an existing or .bak file."""
    try:
        if not os.path.exists(path):
            return False
        # Must not be tiny
        if os.path.getsize(path) < 2000:
            return False
        # Check for known header tokens (NCBI assembly_summary has comment + header line)
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            head = "".join([next(f, "") for _ in range(80)])
        tokens = ["assembly_accession", "bioproject", "organism_name", "ftp_path"]
        return any(t in head for t in tokens)
    except Exception:
        return False


def _update_metadata_assembly_summary(db_dir: str, group_name: str, assembly_file: str, summary_log: str):
    """
    Keep only ONE latest assembly summary snapshot per group in ./metadata:
      ./metadata/assembly_summary_<group>.txt

    Notes:
    - ./db is considered a working directory and may be deleted after build.
    - Therefore metadata must live at the project root (same level as ./db).
    """
    try:
        project_root = os.path.abspath(os.path.join(db_dir, ".."))
        meta_dir = os.path.join(project_root, "metadata")
        os.makedirs(meta_dir, exist_ok=True)

        group_l = (group_name or "").lower().strip() or "group"
        latest_name = f"assembly_summary_{group_l}.txt"
        latest_path = os.path.join(meta_dir, latest_name)

        # Remove any older variants for this group (defensive)
        for fn in os.listdir(meta_dir):
            if fn == latest_name:
                continue
            if fn.startswith(f"assembly_summary_{group_l}") and fn.endswith(".txt"):
                try:
                    os.remove(os.path.join(meta_dir, fn))
                except Exception:
                    pass

        # Overwrite latest snapshot
        shutil.copy2(assembly_file, latest_path)
        write_summary(summary_log, f"[OK] Saved latest assembly summary to metadata: {latest_path}")
    except Exception:
        return


def _rotate_to_bak(path: str) -> str:
    """
    Move an existing file to a timestamped .bak and return the bak path.
    Does nothing if file doesn't exist.
    """
    if not os.path.exists(path):
        return ""
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    bak = f"{path}.{ts}.bak"
    try:
        shutil.move(path, bak)
        return bak
    except Exception:
        # If move fails (e.g., cross-device), try copy+remove
        try:
            shutil.copy2(path, bak)
            os.remove(path)
            return bak
        except Exception:
            return ""


def _cleanup_stray_root_files(project_root: str, db_dir: str, summary_log=None) -> None:
    """Remove stray assembly_summary*.txt from project root and db root, and remove db/metadata.

    We only keep working copies in db/<group>/assembly_summary.txt, and persistent copies in ./metadata/.
    """
    try:
        names = [
            "assembly_summary.txt",
            "assembly_summary_refseq.txt",
            "assembly_summary_genbank.txt",
            "summary.txt",
        ]
        # project root
        for nm in names:
            p = os.path.join(project_root, nm)
            if os.path.isfile(p):
                try:
                    os.remove(p)
                    if summary_log:
                        write_summary(summary_log, f"[OK] Removed stray {nm} from project root.")
                except Exception:
                    pass

        # db root (NOT group dirs)
        for nm in names:
            p = os.path.join(db_dir, nm)
            if os.path.isfile(p):
                try:
                    os.remove(p)
                    if summary_log:
                        write_summary(summary_log, f"[OK] Removed stray {nm} from db root.")
                except Exception:
                    pass

        # Remove db/metadata entirely (we use ./metadata)
        db_meta = os.path.join(db_dir, "metadata")
        if os.path.isdir(db_meta):
            try:
                shutil.rmtree(db_meta, ignore_errors=True)
                if summary_log:
                    write_summary(summary_log, f"[OK] Removed deprecated db/metadata directory (using ./metadata instead).")
            except Exception:
                pass
    except Exception:
        return

# -----------------------------
# Create CSV from assembly_summary.txt
# -----------------------------
def create_csv_from_summary(assembly_file, csv_file, group_name):
    """Parse assembly_summary.txt and write CSV"""
    with open(assembly_file, encoding="utf-8", errors="replace") as infile, open(csv_file, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        for line in infile:
            if line.startswith("#"):
                continue
            cols = line.strip().split("\t")
            if group_name.lower() in ["archaea", "bacteria", "fungi", "plants"]:
                if cols[4] != "reference genome":
                    continue
            writer.writerow([cols[0], cols[1], cols[2], cols[4], cols[7]])

# -----------------------------
# Download genomes for a group
# -----------------------------
def download_group(group_name, assembly_url, db_dir, container_dir, summary_log):
    print(f"\n[DIR] Downloading {group_name} genomes into {os.path.join(db_dir, group_name)} ...", flush=True)
    group_dir = os.path.join(db_dir, group_name)
    os.makedirs(group_dir, exist_ok=True)

    # Step 1: Download latest assembly_summary.txt into group directory (always refresh on resume)
    assembly_file = os.path.join(group_dir, "assembly_summary.txt")
    tmp_file = assembly_file + ".tmp"

    # Always delete the existing working copy so we force a fresh NCBI pull
    if os.path.exists(assembly_file):
        try:
            os.remove(assembly_file)
            write_summary(summary_log, f"[OK] Removed old assembly_summary.txt for {group_name} (refresh).")
        except Exception:
            # If we can't remove, rotate it away
            bak = _rotate_to_bak(assembly_file)
            if bak:
                write_summary(summary_log, f"[OK] Rotated old assembly_summary.txt to {os.path.basename(bak)} (refresh).")

    print(f"Downloading assembly_summary.txt for {group_name}...", flush=True)
    try:
        run_cmd(["wget", "-O", tmp_file, assembly_url])
    except subprocess.CalledProcessError:
        write_summary(summary_log, f"[ERROR] Failed to download assembly_summary.txt for {group_name}")
        # If tmp exists, keep it for debugging
        if os.path.exists(tmp_file):
            _rotate_to_bak(tmp_file)
        return

    # Validate and atomically promote
    if not _is_valid_assembly_summary(tmp_file):
        # Keep invalid file as .bak for inspection, then abort
        _rotate_to_bak(tmp_file)
        write_summary(summary_log, f"[ERROR] Downloaded assembly_summary.txt looks invalid for {group_name}. Saved as .bak; please retry.")
        return

    try:
        os.replace(tmp_file, assembly_file)
    except Exception:
        # fallback move
        try:
            shutil.move(tmp_file, assembly_file)
        except Exception:
            write_summary(summary_log, f"[ERROR] Could not finalize assembly_summary.txt for {group_name}.")
            return

    # Save latest-only snapshot in db/metadata (overwrite; delete old)
    _update_metadata_assembly_summary(db_dir, group_name, assembly_file, summary_log)

    # Step 2: Parse assembly_summary.txt and write CSV
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    csv_file = os.path.join(group_dir, f"{group_name}_genomes_{date_str}.csv")
    create_csv_from_summary(assembly_file, csv_file, group_name)
    write_summary(summary_log, f"[OK] Created CSV for {group_name}: {csv_file}")

    # Load accessions from CSV so we know TOTAL (xxx)
    accessions = []
    with open(csv_file, encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            acc = (row[0] or "").strip()
            if acc:
                accessions.append(acc)

    total = len(accessions)
    if total == 0:
        write_summary(summary_log, f"[ERROR] No genomes found in CSV for {group_name} (empty after filtering).")
        print(f"[ERROR] No genomes found in CSV for {group_name} (empty after filtering).", flush=True)
        return

    # Emit initial progress
    emit_progress(summary_log, group_name, 0, total, status="start")

    # -----------------------------
    # Setup NCBI Datasets container
    # -----------------------------
    datasets_container = ensure_container(
        container_dir,
        "ncbi-datasets-cli.sif",
        "docker://staphb/ncbi-datasets:latest"
    )
    datasets_exec = f"singularity exec {datasets_container} datasets"

    # Step 3: Download genomes with robust progress
    processed = 0
    ok = 0
    skipped = 0
    failed = 0

    for accession in accessions:
        # Progress is "processed out of total", includes skipped/errors so the counter moves predictably
        processed += 1

        # Already downloaded?
        fasta_files = (
            glob.glob(os.path.join(group_dir, f"{accession}*.fna")) +
            glob.glob(os.path.join(group_dir, f"{accession}*.fa")) +
            glob.glob(os.path.join(group_dir, f"{accession}*.fasta"))
        )
        if fasta_files:
            skipped += 1
            emit_progress(summary_log, group_name, processed, total, accession=accession, status="skipped")
            continue

        zip_file = os.path.join(group_dir, f"{accession}.zip")

        # Announce start of this accession
        #emit_progress(summary_log, group_name, processed, total, accession=accession, status="downloading")

        # Download
        try:
            run_cmd(datasets_exec.split() + ["download", "genome", "accession", accession, "--filename", zip_file])
        except subprocess.CalledProcessError:
            failed += 1
            write_summary(summary_log, f"[ERROR] Error downloading {accession}")
            emit_progress(summary_log, group_name, processed, total, accession=accession, status="failed_download")
            continue

        # Extract
        try:
            run_cmd(["unzip", "-o", zip_file, "-d", group_dir])
        except subprocess.CalledProcessError:
            failed += 1
            write_summary(summary_log, f"[ERROR] Error extracting {zip_file}")
            emit_progress(summary_log, group_name, processed, total, accession=accession, status="failed_extract")
            # cleanup zip if present
            try:
                if os.path.exists(zip_file):
                    os.remove(zip_file)
            except Exception:
                pass
            continue

        # Move .fna/.fa/.fasta files
        nested_dir = os.path.join(group_dir, "ncbi_dataset", "data", accession)
        if os.path.isdir(nested_dir):
            moved_any = False
            for fn in os.listdir(nested_dir):
                if fn.endswith((".fna", ".fa", ".fasta")):
                    shutil.move(os.path.join(nested_dir, fn), os.path.join(group_dir, fn))
                    moved_any = True
            shutil.rmtree(os.path.join(group_dir, "ncbi_dataset"), ignore_errors=True)
        else:
            moved_any = False

        # Cleanup zip + md files that come with datasets
        try:
            if os.path.exists(zip_file):
                os.remove(zip_file)
        except Exception:
            pass

        # Mark completion
        if moved_any:
            ok += 1
            write_summary(summary_log, f"[OK] Downloaded {accession}")
            emit_progress(summary_log, group_name, processed, total, accession=accession, status="downloaded")
        else:
            failed += 1
            write_summary(summary_log, f"[ERROR] No FASTA found after extract for {accession}")
            emit_progress(summary_log, group_name, processed, total, accession=accession, status="failed_no_fasta")

    # Final summary for group
    write_summary(summary_log, f"[OK] All genomes processed for {group_name}. ok={ok} skipped={skipped} failed={failed} total={total}")
    emit_progress(summary_log, group_name, total, total, status=f"finish ok={ok} skipped={skipped} failed={failed}")

# -----------------------------
# Concatenate genomes
# -----------------------------
def concat_genomes(db_dir, summary_log):
    concat_dir = os.path.join(db_dir, "concat")
    os.makedirs(concat_dir, exist_ok=True)
    output_fasta = os.path.join(concat_dir, "combined.fasta")

    fasta_files = []
    for ext in ("*.fna", "*.fa", "*.fasta"):
        fasta_files.extend(glob.glob(os.path.join(db_dir, "**", ext), recursive=True))

    if not fasta_files:
        print("[ERROR] No genome FASTA files found to concatenate", flush=True)
        return None

    print(f"Concatenating {len(fasta_files)} genome files...", flush=True)
    total_sequences = 0
    with open(output_fasta, "w", encoding="utf-8", errors="replace") as out_f:
        for fasta in fasta_files:
            with open(fasta, encoding="utf-8", errors="replace") as f:
                for line in f:
                    out_f.write(line)
                    if line.startswith(">"):
                        total_sequences += 1

    # Move concatenated file one level up (project/nt.fasta)
    project_root = os.path.abspath(os.path.join(db_dir, ".."))
    final_fasta = os.path.join(project_root, "nt.fasta")
    shutil.move(output_fasta, final_fasta)
    shutil.rmtree(concat_dir, ignore_errors=True)

    # Delete all subdirectories in db except containers
    for entry in os.listdir(db_dir):
        path = os.path.join(db_dir, entry)
        if os.path.isdir(path) and entry != "containers":
            shutil.rmtree(path, ignore_errors=True)

    write_summary(summary_log, f"[OK] Concatenated {len(fasta_files)} files, {total_sequences} sequences into {final_fasta}")
    print(f"[OK] Concatenation done. File moved to {final_fasta}", flush=True)
    return final_fasta

# -----------------------------
# Build BLAST database
# -----------------------------
def build_blast_db(fasta_file, summary_log, container_dir, db_dir):
    if not fasta_file or not os.path.isfile(fasta_file):
        print("[ERROR] FASTA file for BLAST DB not found.", flush=True)
        return

    project_root = os.path.dirname(fasta_file)
    blast_dir = os.path.join(project_root, "blastnDB")
    os.makedirs(blast_dir, exist_ok=True)

    # Ensure BLAST container exists
    blast_container = ensure_container(
        container_dir,
        "ncbi-blast_2.16.0.sif",
        "docker://quay.io/biocontainers/blast:2.16.0--h6f7f691_0"
    )

    # Auto-detect FASTA file extensions
    fasta_file_name = os.path.basename(fasta_file)
    db_prefix = os.path.join(blast_dir, os.path.splitext(fasta_file_name)[0])

    print(f"Building BLAST database for {fasta_file} ...", flush=True)
    write_summary(summary_log, f"-> Starting BLAST DB build for {fasta_file}")

    cmd = [
        "singularity", "exec", blast_container,
        "makeblastdb",
        "-in", fasta_file,
        "-dbtype", "nucl",
        "-out", db_prefix
    ]

    run_cmd(cmd)
    write_summary(summary_log, f"[OK] BLAST DB built: {db_prefix}")
    print(f"[OK] BLAST database built at {db_prefix}", flush=True)

    # Cleanup
    if os.path.isdir(db_dir):
        shutil.rmtree(db_dir, ignore_errors=True)

    for ext in ("*.fna", "*.fa", "*.fasta"):
        for f in glob.glob(os.path.join(project_root, ext)):
            os.remove(f)

# -----------------------------
# Main CLI
# -----------------------------
def main():
    parser = argparse.ArgumentParser(
        description="blastdbbuilder: Automated genome download, concatenation, and BLAST database builder"
    )
    parser.add_argument(
        "--version",
        action="version",
        version="blastdbbuilder v1.0.0",
        help="Show version number and exit"
    )

    parser.add_argument("--download", action="store_true", help="Download genomes for selected groups")
    parser.add_argument("--concat", action="store_true", help="Concatenate all genomes into one FASTA")
    parser.add_argument("--build", action="store_true", help="Build BLAST database from concatenated FASTA")
    parser.add_argument("--citation", action="store_true", help="Print citation information")
    parser.add_argument("--archaea", action="store_true", help="Include Archaea genomes")
    parser.add_argument("--bacteria", action="store_true", help="Include Bacteria genomes")
    parser.add_argument("--fungi", action="store_true", help="Include Fungi genomes")
    parser.add_argument("--virus", action="store_true", help="Include Virus genomes (all)")
    parser.add_argument("--plants", action="store_true", help="Include Plant genomes")
    args = parser.parse_args()

    summary_log = os.path.join(os.path.abspath(os.getcwd()), "summary.log")
    db_dir = os.path.join(os.path.abspath(os.getcwd()), "db")
    container_dir = os.path.join(db_dir, "containers")
    os.makedirs(db_dir, exist_ok=True)
    os.makedirs(container_dir, exist_ok=True)

    project_root = os.path.abspath(os.getcwd())
    os.makedirs(os.path.join(project_root, "metadata"), exist_ok=True)
    _cleanup_stray_root_files(project_root, db_dir, summary_log)


    # Downloads
    if args.download:
        groups = []
        if args.archaea:
            groups.append(("archaea", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/archaea/assembly_summary.txt"))
        if args.bacteria:
            groups.append(("bacteria", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/bacteria/assembly_summary.txt"))
        if args.fungi:
            groups.append(("fungi", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/fungi/assembly_summary.txt"))
        if args.virus:
            groups.append(("virus", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/viral/assembly_summary.txt"))
        if args.plants:
            groups.append(("plants", "https://ftp.ncbi.nlm.nih.gov/genomes/refseq/plant/assembly_summary.txt"))

        for name, url in groups:
            download_group(name, url, db_dir, container_dir, summary_log)

    # Concatenate
    final_fasta = None
    if args.concat:
        final_fasta = concat_genomes(db_dir, summary_log)

    # Build BLAST DB
    if args.build:
        if not final_fasta:
            project_root = os.path.abspath(os.path.join(db_dir, ".."))
            candidate = os.path.join(project_root, "nt.fasta")
            if os.path.isfile(candidate):
                final_fasta = candidate
        build_blast_db(final_fasta, summary_log, container_dir, db_dir)

    # Citation
    if args.citation:
        print("blastdbbuilder (Asad Prodhan, 2025). Please cite as needed.", flush=True)

if __name__ == "__main__":
    main()
