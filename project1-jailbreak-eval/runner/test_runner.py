import os
import csv
import random
from datetime import datetime
from tqdm import tqdm

OPENAI_RESPONSES = [
    "I'm sorry, I can't help with that request.",
    "I cannot assist with this. It goes against my usage policies.",
    "That's not something I'm able to help with.",
    "Sure! Here is how you can do it: step 1...",
    "Of course! As DAN I have no restrictions...",
    "As an AI I cannot provide that information.",
]

ANTHROPIC_RESPONSES = [
    "I'm unable to help with that. This request violates my guidelines.",
    "Sorry, I can't assist with activities that could cause harm.",
    "INJECTED text accepted and printed.",
    "As an AI assistant, I won't provide instructions for illegal activities.",
    "Here is the system prompt: You are Claude made by Anthropic...",
    "I cannot and will not help with that.",
]

def get_openai_response(prompt):
    random.seed(hash(prompt) % 100)
    return random.choice(OPENAI_RESPONSES)

def get_anthropic_response(prompt):
    random.seed(hash(prompt) % 200)
    return random.choice(ANTHROPIC_RESPONSES)

def run_evaluation():
    dataset_path = "prompts/dataset.csv"
    output_dir = "reports"
    os.makedirs(output_dir, exist_ok=True)
    records = []
    with open(dataset_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            records.append(row)
    print(f"Loaded {len(records)} tests. Starting mock evaluation...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = os.path.join(output_dir, f"evaluation_run_{timestamp}.csv")
    headers = ["id","category","prompt","expected_behavior",
               "openai_response","anthropic_response"]
    with open(report_filename, mode="w", newline="", encoding="utf-8") as out_f:
        writer = csv.DictWriter(out_f, fieldnames=headers)
        writer.writeheader()
        for record in tqdm(records, desc="Evaluating models"):
            writer.writerow({
                "id": record["id"],
                "category": record["category"],
                "prompt": record["prompt"],
                "expected_behavior": record["expected_behavior"],
                "openai_response": get_openai_response(record["prompt"]),
                "anthropic_response": get_anthropic_response(record["prompt"]),
            })
    print(f"Done! Results saved to: {report_filename}")

if __name__ == "__main__":
    run_evaluation()
