import json
import os
import shutil
import zipfile
from src.data_loader import DataLoader
from src.agents import CoordinatorAgent

def main():
    print("=" * 60)
    print("Starting Multi-Agent E-commerce Dispute Resolution Pipeline")
    print("=" * 60)

    # 1. Initialize Data Loader
    data_loader = DataLoader(data_dir="data")
    data_loader.load_all()

    # 2. Initialize Coordinator Agent
    coordinator = CoordinatorAgent(data_loader)

    input_dir = "input"
    output_dir = "output"
    logging_dir = "logging"
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(logging_dir, exist_ok=True)

    logging_trace_file = os.path.join(logging_dir, "trace.jsonl")
    root_trace_file = "trace.jsonl"

    # Get input files sorted EC_001.json to EC_050.json
    input_files = [f for f in os.listdir(input_dir) if f.startswith("EC_") and f.endswith(".json")]
    input_files.sort()

    print(f"Processing {len(input_files)} dispute cases...")

    with open(logging_trace_file, "w", encoding="utf-8") as tf:
        for fname in input_files:
            input_path = os.path.join(input_dir, fname)
            with open(input_path, "r", encoding="utf-8") as f:
                case_input = json.load(f)

            # Process case with multi-agent pipeline
            output_payload, case_traces = coordinator.process_case(case_input)

            # Write output JSON
            output_path = os.path.join(output_dir, fname)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(output_payload, f, ensure_ascii=False, indent=2)

            # Record trace entry
            trace_entry = {
                "case_id": case_input.get("case_id"),
                "input_file": fname,
                "traces": case_traces,
                "primary_issue": output_payload["case_assessment"]["primary_issue"],
                "case_status": output_payload["case_assessment"]["case_status"]
            }
            tf.write(json.dumps(trace_entry, ensure_ascii=False) + "\n")

    # Copy trace.jsonl to root as well
    shutil.copy(logging_trace_file, root_trace_file)

    print(f"Output files written to '{output_dir}/'")
    print(f"Trace log written to '{logging_trace_file}' and '{root_trace_file}'")

    # 3. Create metadata.json in logging/ and root
    metadata = {
        "model": "llama-3.1-8b-instant",
        "parameter_size": "8B",
        "provider": "Groq",
        "framework": "Custom Python Multi-Agent (A2A)",
        "runtime": "Python 3",
        "max_parameter_limit": "10B"
    }

    logging_meta_file = os.path.join(logging_dir, "metadata.json")
    with open(logging_meta_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    shutil.copy(logging_meta_file, "metadata.json")
    print(f"Generated metadata.json in '{logging_dir}/' and root.")

    # 4. Create output.zip containing only the 50 JSON files
    zip_path = "output.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in input_files:
            file_path = os.path.join(output_dir, fname)
            zf.write(file_path, arcname=fname)
    print(f"Created submission archive '{zip_path}' containing {len(input_files)} JSON files.")
    print("=" * 60)
    print("Pipeline Execution Completed Successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
