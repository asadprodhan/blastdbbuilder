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
from blastdbbuilder import __version__

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
# Container engine helper
# -----------------------------
def get_container_engine():
    engine = shutil.which("apptainer") or shutil.which("singularity")
    if not engine:
        raise RuntimeError("Neither apptainer nor singularity was found in PATH.")
    return engine

# -----------------------------
# Ensure container exists
# -----------------------------
def ensure_container(container_dir, container_name, image):
    container_path = os.path.join(container_dir, container_name)
    if not os.path.isfile(container_path):
        print(f"[INFO] Downloading container: {container_name}", flush=True)
        os.makedirs(container_dir, exist_ok=True)
        engine = get_container_engine()
        run_cmd([engine, "pull", container_path, image])
    return container_path

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
    print(f"\n[INFO] Downloading {group_name} genomes into {os.path.join(db_dir, group_name)} ...", flush=True)
    group_dir = os.path.join(db_dir, group_name)
    os.makedirs(group_dir, exist_ok=True)
    completed_log = os.path.join(group_dir, "downloaded_accessions.txt")
    completed = set()
    if os.path.exists(completed_log):
        with open(completed_log, encoding="utf-8", errors="replace") as f:
            for line in f:
                acc = line.strip()
                if acc:
                    completed.add(acc)

    # Step 1: Download assembly_summary.txt
    assembly_file = os.path.join(group_dir, "assembly_summary.txt")
    print(f"Downloading assembly_summary.txt for {group_name}...", flush=True)
    try:
        run_cmd(["wget", "-O", assembly_file, assembly_url])
    except subprocess.CalledProcessError:
        write_summary(summary_log, f"[ERROR] Failed to download assembly_summary.txt for {group_name}")
        return

    # Step 2: Parse assembly_summary.txt and write CSV
    date_str = datetime.date.today().strftime("%Y-%m-%d")
    csv_file = os.path.join(group_dir, f"{group_name}_genomes_{date_str}.csv")
    create_csv_from_summary(assembly_file, csv_file, group_name)
    write_summary(summary_log, f"[OK] Created CSV for {group_name}: {csv_file}")

    # Load accessions from CSV so we know TOTAL
    accessions = []
    seen = set()
    with open(csv_file, encoding="utf-8", errors="replace") as f:
        reader = csv.reader(f)
        for row in reader:
            if not row:
                continue
            acc = (row[0] or "").strip()
            if acc and acc not in seen:
                accessions.append(acc)
                seen.add(acc) 

    total = len(accessions)
    if total == 0:
        write_summary(summary_log, f"[ERROR] No genomes found in CSV for {group_name} (empty after filtering).")
        print(f"[ERROR] No genomes found in CSV for {group_name} (empty after filtering).", flush=True)
        return

    # Emit initial progress
    emit_progress(summary_log, group_name, 0, total, status="start")

    # Setup NCBI Datasets container
    datasets_container = ensure_container(
        container_dir,
        "ncbi-datasets-cli.sif",
        "docker://staphb/ncbi-datasets:latest"
    )
    engine = get_container_engine()
    bind_args = ["-B", "/data:/data"] if os.path.exists("/data") else []

    # Step 3: Download genomes with robust progress
    processed = 0
    ok = 0
    skipped = 0
    failed = 0

    for accession in accessions:
        processed += 1

        fasta_files = (
            glob.glob(os.path.join(group_dir, f"{accession}*.fna")) +
            glob.glob(os.path.join(group_dir, f"{accession}*.fa")) +
            glob.glob(os.path.join(group_dir, f"{accession}*.fasta"))
        )
        if accession in completed or fasta_files:
            skipped += 1
            emit_progress(summary_log, group_name, processed, total, accession=accession, status="skipped")
            continue

        zip_file = os.path.join(group_dir, f"{accession}.zip")

        # Announce start of this accession
        #emit_progress(summary_log, group_name, processed, total, accession=accession, status="downloading")

        # Download
        try:
            run_cmd([engine, "exec", *bind_args, datasets_container, "datasets", "download", "genome", "accession", accession, "--filename", zip_file])
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

        # Cleanup zip
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
            if accession not in completed:
                with open(completed_log, "a", encoding="utf-8") as f:
                    f.write(accession + "\n")
                completed.add(accession)
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

    project_root = os.path.abspath(os.path.join(db_dir, ".."))
    final_fasta = os.path.join(project_root, "nt.fasta")
    shutil.move(output_fasta, final_fasta)
    shutil.rmtree(concat_dir, ignore_errors=True)

    for entry in os.listdir(db_dir):
        path = os.path.join(db_dir, entry)
        if os.path.isdir(path) and entry != "containers":
            shutil.rmtree(path, ignore_errors=True)

    write_summary(summary_log, f"[OK] Concatenated {len(fasta_files)} files, {total_sequences} sequences into {final_fasta}")
    print(f"[OK] Concatenation done. File moved to {final_fasta}", flush=True)
    return final_fasta

# -----------------------------
# Custom FASTA input + BLAST database build
# -----------------------------
FASTA_EXTENSIONS = (".fasta", ".fa", ".fna", ".fas")


def find_fasta_files(input_dir):
    """Return FASTA files directly inside input_dir, sorted by filename.

    Generated blastdbbuilder output is excluded automatically because blastnDB
    is a subdirectory and this scan is intentionally non-recursive.
    """
    input_dir = os.path.abspath(os.path.expanduser(input_dir))
    if not os.path.isdir(input_dir):
        raise ValueError(f"Input directory does not exist: {input_dir}")

    files = []
    for name in sorted(os.listdir(input_dir)):
        path = os.path.join(input_dir, name)
        if os.path.isfile(path) and name.lower().endswith(FASTA_EXTENSIONS):
            files.append(path)
    return files


def validate_fasta_file(path):
    """Perform a lightweight FASTA validation and return sequence count."""
    headers = 0
    saw_sequence = False
    with open(path, "r", encoding="utf-8", errors="replace") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                continue
            if line.startswith(">"):
                headers += 1
            else:
                saw_sequence = True
    if headers == 0 or not saw_sequence:
        raise ValueError(f"Not a valid FASTA file (no FASTA records found): {path}")
    return headers


def prepare_input_fasta(input_dir, blast_dir, summary_log):
    """Find FASTA input(s), validate them, and concatenate when necessary.

    Returns (fasta_for_build, temporary_combined, fasta_files, total_sequences).
    Original FASTA files are never modified or deleted.
    """
    fasta_files = find_fasta_files(input_dir)
    if not fasta_files:
        raise ValueError(
            f"No FASTA files found in {input_dir}. Supported extensions: "
            + ", ".join(FASTA_EXTENSIONS)
        )

    total_sequences = 0
    for fasta in fasta_files:
        total_sequences += validate_fasta_file(fasta)

    if len(fasta_files) == 1:
        write_summary(summary_log, f"[OK] Found 1 FASTA file with {total_sequences} sequences: {fasta_files[0]}")
        return fasta_files[0], False, fasta_files, total_sequences

    os.makedirs(blast_dir, exist_ok=True)
    combined = os.path.join(blast_dir, ".blastdbbuilder_combined.fasta")
    print(f"[INFO] Found {len(fasta_files)} FASTA files. Concatenating automatically...", flush=True)
    with open(combined, "w", encoding="utf-8") as out_f:
        for fasta in fasta_files:
            with open(fasta, "r", encoding="utf-8", errors="replace") as in_f:
                shutil.copyfileobj(in_f, out_f)
                # Ensure records from adjacent files cannot run together.
                out_f.write("\n")

    write_summary(
        summary_log,
        f"[OK] Concatenated {len(fasta_files)} FASTA files ({total_sequences} sequences) for BLAST DB build"
    )
    return combined, True, fasta_files, total_sequences


def _makeblastdb_command(fasta_file, db_prefix, container_dir):
    """Return a command for makeblastdb, preferring a local BLAST+ installation."""
    local_makeblastdb = shutil.which("makeblastdb")
    if local_makeblastdb:
        return [
            local_makeblastdb,
            "-in", fasta_file,
            "-dbtype", "nucl",
            "-out", db_prefix,
        ]

    blast_container = ensure_container(
        container_dir,
        "ncbi-blast_2.16.0.sif",
        "docker://quay.io/biocontainers/blast:2.16.0--h6f7f691_0"
    )
    engine = get_container_engine()

    # Bind the input/output directory explicitly so custom FASTA folders outside
    # /data are available inside Apptainer/Singularity as well.
    bind_root = os.path.dirname(os.path.abspath(fasta_file))
    bind_args = ["-B", f"{bind_root}:{bind_root}"]
    if os.path.exists("/data") and bind_root != "/data":
        bind_args.extend(["-B", "/data:/data"])

    return [
        engine, "exec", *bind_args, blast_container,
        "makeblastdb",
        "-in", fasta_file,
        "-dbtype", "nucl",
        "-out", db_prefix,
    ]


def build_blast_db_from_directory(input_dir, summary_log, container_dir):
    """Build blastnDB/nt.* from one or more FASTA files in input_dir."""
    input_dir = os.path.abspath(os.path.expanduser(input_dir))
    blast_dir = os.path.join(input_dir, "blastnDB")
    os.makedirs(blast_dir, exist_ok=True)
    db_prefix = os.path.join(blast_dir, "nt")

    fasta_for_build = None
    temporary_combined = False
    try:
        fasta_for_build, temporary_combined, fasta_files, total_sequences = prepare_input_fasta(
            input_dir, blast_dir, summary_log
        )

        print(f"[INFO] Input directory: {input_dir}", flush=True)
        print(f"[INFO] FASTA files: {len(fasta_files)}", flush=True)
        print(f"[INFO] Sequences: {total_sequences}", flush=True)
        print(f"[INFO] Output database: {db_prefix}", flush=True)
        write_summary(summary_log, f"-> Starting BLAST DB build: {db_prefix}")

        cmd = _makeblastdb_command(fasta_for_build, db_prefix, container_dir)
        run_cmd(cmd)

        write_summary(summary_log, f"[OK] BLAST DB built: {db_prefix}")
        print(f"[OK] BLAST database built successfully: {db_prefix}", flush=True)
        print("[OK] Original FASTA file(s) were preserved.", flush=True)
        return db_prefix
    finally:
        if temporary_combined and fasta_for_build and os.path.isfile(fasta_for_build):
            try:
                os.remove(fasta_for_build)
            except OSError:
                pass


# -----------------------------
# Legacy concatenation/build helpers (kept for existing CLI workflows)
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

    project_root = os.path.abspath(os.path.join(db_dir, ".."))
    final_fasta = os.path.join(project_root, "nt.fasta")
    shutil.move(output_fasta, final_fasta)
    shutil.rmtree(concat_dir, ignore_errors=True)

    for entry in os.listdir(db_dir):
        path = os.path.join(db_dir, entry)
        if os.path.isdir(path) and entry != "containers":
            shutil.rmtree(path, ignore_errors=True)

    write_summary(summary_log, f"[OK] Concatenated {len(fasta_files)} files, {total_sequences} sequences into {final_fasta}")
    print(f"[OK] Concatenation done. File moved to {final_fasta}", flush=True)
    return final_fasta


def build_blast_db(fasta_file, summary_log, container_dir, db_dir):
    """Legacy build path. Output basename is now always blastnDB/nt."""
    if not fasta_file or not os.path.isfile(fasta_file):
        print("[ERROR] FASTA file for BLAST DB not found.", flush=True)
        return None

    project_root = os.path.dirname(os.path.abspath(fasta_file))
    blast_dir = os.path.join(project_root, "blastnDB")
    os.makedirs(blast_dir, exist_ok=True)
    db_prefix = os.path.join(blast_dir, "nt")

    print(f"Building BLAST database for {fasta_file} ...", flush=True)
    write_summary(summary_log, f"-> Starting BLAST DB build for {fasta_file}")
    cmd = _makeblastdb_command(fasta_file, db_prefix, container_dir)
    run_cmd(cmd)
    write_summary(summary_log, f"[OK] BLAST DB built: {db_prefix}")
    print(f"[OK] BLAST database built at {db_prefix}", flush=True)
    return db_prefix

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
        version=f"blastdbbuilder v{__version__}",
        help="Show version number and exit"
    )

    parser.add_argument("--download", action="store_true", help="Download genomes for selected groups")
    parser.add_argument("--concat", action="store_true", help="Concatenate all genomes into one FASTA")
    parser.add_argument("--build", action="store_true", help="Build BLAST database")
    parser.add_argument(
        "--input-dir",
        metavar="DIR",
        help="Directory containing one or more FASTA files. With --build, multiple FASTA files are concatenated automatically and output is DIR/blastnDB/nt.*"
    )
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

    final_fasta = None
    if args.concat:
        final_fasta = concat_genomes(db_dir, summary_log)

    if args.build:
        if args.input_dir:
            input_dir = os.path.abspath(os.path.expanduser(args.input_dir))
            summary_log = os.path.join(input_dir, "summary.log")
            container_dir = os.environ.get(
                "BLASTDBBUILDER_CONTAINER_DIR",
                os.path.join(os.path.expanduser("~"), ".cache", "blastdbbuilder", "containers")
            )
            os.makedirs(container_dir, exist_ok=True)
            try:
                build_blast_db_from_directory(input_dir, summary_log, container_dir)
            except (ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
                print(f"[ERROR] {exc}", file=sys.stderr, flush=True)
                sys.exit(1)
        else:
            if not final_fasta:
                project_root = os.path.abspath(os.path.join(db_dir, ".."))
                candidate = os.path.join(project_root, "nt.fasta")
                if os.path.isfile(candidate):
                    final_fasta = candidate
            build_blast_db(final_fasta, summary_log, container_dir, db_dir)

    if args.citation:
        print("blastdbbuilder (Asad Prodhan, 2025). Please cite as needed.", flush=True)

if __name__ == "__main__":
    main()
