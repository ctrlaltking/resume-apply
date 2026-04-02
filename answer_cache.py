"""
Persist answers to unknown form questions so you only answer each once.
"""
import json
from pathlib import Path

CACHE_FILE = Path(__file__).parent / "answer_cache.json"


def load() -> dict:
    if CACHE_FILE.exists():
        return json.loads(CACHE_FILE.read_text())
    return {}


def save(cache: dict):
    CACHE_FILE.write_text(json.dumps(cache, indent=2))


def get_or_ask(question: str, cache: dict) -> str:
    """Return cached answer or prompt user and cache the result."""
    key = question.strip().lower()
    if key in cache:
        print(f"\n[CACHED] {question}\n  → {cache[key]}")
        return cache[key]

    print(f"\n[UNKNOWN FIELD] {question}")
    answer = input("  Your answer: ").strip()
    cache[key] = answer
    save(cache)
    return answer
