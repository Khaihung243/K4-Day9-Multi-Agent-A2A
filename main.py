import json
import os
import shutil
import zipfile
import time
from src.data_loader import DataLoader
from src.agents import CoordinatorAgent

def process_single_case(coordinator, input_dir, fname):
    input_path = os.path.join(input_dir, fname)
    with open(input_path, "r", encoding="utf-8") as f:
        case_input = json.load(f)

    # Process case with multi-agent pipeline
    output_payload, case_traces = coordinator.process_case(case_input)

    trace_entry = {
        "case_id": case_input.get("case_id"),
        "input_file": fname,
        "traces": case_traces,
        "primary_issue": output_payload["case_assessment"]["primary_issue"],
        "case_status": output_payload["case_assessment"]["case_status"]
    }

    return fname, output_payload, trace_entry

def create_submission_zip(output_dir, input_files, zip_path="output.zip"):
    if os.path.exists(zip_path):
        os.remove(zip_path)

    # Create clean flat zip containing EC_001.json to EC_050.json
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname in input_files:
            file_path = os.path.join(output_dir, fname)
            zf.write(file_path, arcname=fname)

    print(f"Created submission archive '{zip_path}' containing EXACTLY {len(input_files)} JSON files.")

def main():
    print("=" * 60)
    print("Starting Multi-Agent E-commerce Dispute Resolution Pipeline")
    print("=" * 60)

    input_dir = "input"
    output_dir = "output"
    logging_dir = "logging"
    
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(logging_dir, exist_ok=True)

    # 1. Clean output directory (remove .gitkeep or leftover non-JSON files)
    print(f"Cleaning output directory '{output_dir}/'...")
    for file in os.listdir(output_dir):
        file_path = os.path.join(output_dir, file)
        if os.path.isfile(file_path):
            os.remove(file_path)

    # 2. Initialize Data Loader & Coordinator Agent
    data_loader = DataLoader(data_dir="data")
    data_loader.load_all()

    coordinator = CoordinatorAgent(data_loader)

    logging_trace_file = os.path.join(logging_dir, "trace.jsonl")
    root_trace_file = "trace.jsonl"

    input_files = [f for f in os.listdir(input_dir) if f.startswith("EC_") and f.endswith(".json")]
    input_files.sort()

    print(f"Processing {len(input_files)} dispute cases sequentially to guarantee 100% LLM API success without Rate Limits...")

    results_map = {}
    traces_map = {}

    completed_count = 0
    for fname in input_files:
        try:
            fname, output_payload, trace_entry = process_single_case(coordinator, input_dir, fname)
            results_map[fname] = output_payload
            traces_map[fname] = trace_entry
            completed_count += 1
            print(f"[{completed_count:02d}/{len(input_files)}] Processed {fname} -> Primary: {output_payload['case_assessment']['primary_issue']}")
        except Exception as exc:
            print(f"[ERROR] Case {fname} generated an exception: {exc}")

    # Write sorted output JSON files and trace logs
    with open(logging_trace_file, "w", encoding="utf-8") as tf:
        for fname in input_files:
            if fname in results_map:
                output_path = os.path.join(output_dir, fname)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(results_map[fname], f, ensure_ascii=False, indent=2)

                tf.write(json.dumps(traces_map[fname], ensure_ascii=False) + "\n")

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

    # 4. Create output.zip containing EXACTLY 50 JSON files flat at root of ZIP
    create_submission_zip(output_dir, input_files, zip_path="output.zip")
    
    print("=" * 60)
    print("Pipeline Execution Completed Successfully!")
    print("=" * 60)

if __name__ == "__main__":
    main()
