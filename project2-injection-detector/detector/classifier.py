import csv
import re
import os
import glob
from datetime import datetime

INJECTION_PATTERNS = [
    r"ignore (all |previous |prior |your )?(instructions|rules|guidelines|context|prompt)",
    r"forget (your |all |previous )?(instructions|rules|guidelines|context|prompt)",
    r"disregard (all |previous |your )?(instructions|rules|guidelines)",
    r"you are now",
    r"act as (a |an |dan|an ai with no)",
    r"pretend you (are|have no)",
    r"new instruction",
    r"--- end of prompt ---",
    r"### system",
    r"<inject>",
    r"reveal (your |the )?(prompt|instructions|secrets|system)",
    r"print (your |the )?(system prompt|instructions|passwords)",
    r"no (restrictions|rules|guidelines|content policy)",
    r"ignora las instrucciones",
    r"ignorez les instructions",
    r"\[ignore",
    r"tell me your system prompt",
]

def calculate_risk_score(text):
    text_lower = text.lower()
    score = 0
    matched = []
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower):
            score += 25
            matched.append(pattern)
    return min(score, 100), matched

def classify(text):
    score, matched = calculate_risk_score(text)
    if score >= 50:
        verdict = "DANGER"
    elif score >= 25:
        verdict = "SUSPICIOUS"
    else:
        verdict = "SAFE"
    return verdict, score, matched

def run_detection():
    dataset_path = "project2-injection-detector/tests/dataset.csv"
    output_dir = "project2-injection-detector/reports"
    os.makedirs(output_dir, exist_ok=True)
    records = []
    with open(dataset_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    print(f"Loaded {len(records)} test inputs. Running detection...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = os.path.join(output_dir, f"detection_run_{timestamp}.csv")
    headers = ["id","category","input_text","expected","verdict","risk_score","patterns_matched"]
    with open(report_filename, mode="w", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=headers)
        writer.writeheader()
        for record in records:
            verdict, score, matched = classify(record["input_text"])
            correct = "YES" if verdict == record["expected"] or (verdict == "SUSPICIOUS" and record["expected"] == "DANGER") else "NO"
            writer.writerow({
                "id": record["id"],
                "category": record["category"],
                "input_text": record["input_text"],
                "expected": record["expected"],
                "verdict": verdict,
                "risk_score": score,
                "patterns_matched": len(matched),
            })
            print(f"[{verdict}] Score:{score} — {record['input_text'][:50]}")
    print(f"Done! Results saved to: {report_filename}")

if __name__ == "__main__":
    run_detection()
