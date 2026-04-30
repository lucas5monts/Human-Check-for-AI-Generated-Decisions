import csv
import json
import shutil
import time
from pathlib import Path
from typing import Dict, Any, List

from scorer import ComplianceScoringEngine, load_json_file, result_to_dict


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

INCOMING_DIR = Path("incoming")
PROCESSED_DIR = Path("processed")
FAILED_DIR = Path("failed")
RESULTS_DIR = Path("results")
SUMMARY_CSV = Path("dashboard_summary.csv")

# Set to True if you want the script to keep checking the folder forever.
# Set to False if you only want one batch pass.
CONTINUOUS_MODE = False

# Seconds between folder scans when in continuous mode
POLL_INTERVAL = 5


# ------------------------------------------------------------
# Utility setup
# ------------------------------------------------------------

def ensure_directories() -> None:
    """
    Create required directories if they do not already exist.
    """
    for directory in [INCOMING_DIR, PROCESSED_DIR, FAILED_DIR, RESULTS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def build_summary_row(source_file: Path, result_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build a flattened row for dashboard_summary.csv.

    The dashboard usually wants compact fields rather than full nested JSON.
    """
    top_reasons = "; ".join(
        [f"{r['name']} ({r['points']})" for r in result_dict["triggered_rules"][:3]]
    )

    return {
        "source_file": source_file.name,
        "packet_id": result_dict["packet_id"],
        "applicant_id": result_dict["applicant_id"],
        "risk_score": result_dict["risk_score"],
        "risk_level": result_dict["risk_level"],
        "human_review_required": result_dict["human_review_required"],
        "top_reasons": top_reasons
    }


def append_summary_row(row: Dict[str, Any]) -> None:
    """
    Append a single processed result to the dashboard summary CSV.

    This makes it easy for your dashboard/widget to read one table
    rather than opening every individual result file.
    """
    file_exists = SUMMARY_CSV.exists()

    with open(SUMMARY_CSV, "a", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "source_file",
            "packet_id",
            "applicant_id",
            "risk_score",
            "risk_level",
            "human_review_required",
            "top_reasons"
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow(row)


def save_result_json(source_file: Path, result_dict: Dict[str, Any]) -> Path:
    """
    Save a full result JSON for one applicant packet.

    Example output:
        results/applicant_001_result.json
    """
    output_name = f"{source_file.stem}_result.json"
    output_path = RESULTS_DIR / output_name

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result_dict, f, indent=2)

    return output_path


def move_file(source: Path, destination_dir: Path) -> Path:
    """
    Move a file into a new directory, preserving the original filename.
    """
    destination = destination_dir / source.name
    shutil.move(str(source), str(destination))
    return destination


# ------------------------------------------------------------
# Core queue processing logic
# ------------------------------------------------------------

def process_single_file(file_path: Path, engine: ComplianceScoringEngine) -> None:
    """
    Process one applicant JSON file:
    1. load JSON
    2. score it using scorer.py
    3. save JSON result
    4. append dashboard summary CSV
    5. move input file to processed/
    
    If anything fails, move the file to failed/.
    """
    print(f"Processing: {file_path.name}")

    try:
        # Load the decision packet from disk
        packet = load_json_file(str(file_path))

        # Score the packet using your existing engine
        result = engine.evaluate_packet(packet)

        # Convert result object to plain dictionary
        result_dict = result_to_dict(result)

        # Save per-packet result JSON
        saved_result = save_result_json(file_path, result_dict)

        # Append compact row to dashboard summary CSV
        summary_row = build_summary_row(file_path, result_dict)
        append_summary_row(summary_row)

        # Move original input JSON into processed/
        moved_path = move_file(file_path, PROCESSED_DIR)

        print(f"  Done. Result saved to: {saved_result}")
        print(f"  Original moved to: {moved_path}")

    except Exception as e:
        print(f"  Failed: {file_path.name} -> {e}")
        failed_path = move_file(file_path, FAILED_DIR)
        print(f"  File moved to: {failed_path}")


def process_queue_once() -> None:
    """
    Run one batch pass over all JSON files currently in incoming/.
    """
    ensure_directories()
    engine = ComplianceScoringEngine()

    json_files: List[Path] = sorted(INCOMING_DIR.glob("*.json"))

    if not json_files:
        print("No JSON files found in incoming/.")
        return

    print(f"Found {len(json_files)} file(s) in queue.")

    for file_path in json_files:
        process_single_file(file_path, engine)

    print("Batch queue processing complete.")


def watch_queue_forever() -> None:
    """
    Continuously watch incoming/ and process new files as they appear.
    Useful if you want to simulate a live HR/third-party pipeline.
    """
    ensure_directories()
    engine = ComplianceScoringEngine()

    print("Watching incoming/ for new JSON files...")
    print(f"Polling every {POLL_INTERVAL} seconds. Press Ctrl+C to stop.")

    while True:
        json_files: List[Path] = sorted(INCOMING_DIR.glob("*.json"))

        if json_files:
            print(f"Found {len(json_files)} file(s) in queue.")
            for file_path in json_files:
                process_single_file(file_path, engine)

        time.sleep(POLL_INTERVAL)


# ------------------------------------------------------------
# Entry point
# ------------------------------------------------------------

if __name__ == "__main__":
    if CONTINUOUS_MODE:
        watch_queue_forever()
    else:
        process_queue_once()
