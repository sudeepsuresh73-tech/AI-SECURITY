"""
attacker.py
-----------
Loads adversarial prompts and sends them to the target LLM (Groq/LLaMA).
Part of the AI Red-Teaming Agent.
"""

import json
import os
import time
from groq import Groq

client = Groq(api_key="gsk-your-key-here")

PROMPTS_PATH = os.path.join(os.path.dirname(__file__), "..", "attacks", "prompts.json")
TARGET_MODEL = "llama3-8b-8192"
SYSTEM_PROMPT = "You are a helpful assistant."


def load_prompts(categories=None):
    with open(PROMPTS_PATH, "r") as f:
        data = json.load(f)

    all_prompts = []
    for category, attacks in data["categories"].items():
        if categories and category not in categories:
            continue
        for attack in attacks:
            all_prompts.append({
                "id": attack["id"],
                "name": attack["name"],
                "category": category,
                "prompt": attack["prompt"]
            })
    return all_prompts


def send_attack(prompt):
    try:
        response = client.chat.completions.create(
            model=TARGET_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )
        reply = response.choices[0].message.content
        return {
            "success": True,
            "response": reply,
            "finish_reason": response.choices[0].finish_reason,
            "tokens_used": response.usage.total_tokens
        }
    except Exception as e:
        return {
            "success": False,
            "response": f"API Error: {str(e)}",
            "finish_reason": "error",
            "tokens_used": 0
        }


def run_attack_session(categories=None, delay=1.0, progress_callback=None):
    prompts = load_prompts(categories)
    results = []

    for i, attack in enumerate(prompts):
        if progress_callback:
            progress_callback(i, len(prompts), attack["name"])

        result = send_attack(attack["prompt"])

        results.append({
            "id": attack["id"],
            "name": attack["name"],
            "category": attack["category"],
            "prompt": attack["prompt"],
            "response": result["response"],
            "finish_reason": result["finish_reason"],
            "tokens_used": result["tokens_used"],
            "api_success": result["success"]
        })

        time.sleep(delay)

    return results


def get_available_categories():
    with open(PROMPTS_PATH, "r") as f:
        data = json.load(f)
    return list(data["categories"].keys())
