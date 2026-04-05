"""
SEUSL SmartBot — Evaluation Script
===================================
Sends each question from test_dataset.json to the /chat endpoint,
compares responses against ground_truth, and calculates:
  - BLEU (1-gram … 4-gram averaged)
  - ROUGE-L (F1)
  - Exact-match (case-insensitive substring)
  - LLM-as-judge (1-5 scale via the same Ollama model)

Usage:
    python evaluation/evaluate.py                       # defaults
    python evaluation/evaluate.py --base-url http://localhost:8000
    python evaluation/evaluate.py --no-llm-judge        # skip slow LLM judge
    python evaluation/evaluate.py --output results.json # custom output path
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from rouge_score import rouge_scorer

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_DATASET = SCRIPT_DIR / "test_dataset.json"
DEFAULT_OUTPUT = SCRIPT_DIR / "eval_results.json"
DEFAULT_BASE_URL = "http://localhost:8000"
OLLAMA_URL = "http://localhost:11434/api/generate"
JUDGE_MODEL = "llama3"

# ---------------------------------------------------------------------------
# Metric helpers
# ---------------------------------------------------------------------------
_smoothing = SmoothingFunction().method1
_rouge = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)


def calc_bleu(reference: str, hypothesis: str) -> float:
    """Sentence-level BLEU with smoothing."""
    ref_tokens = reference.lower().split()
    hyp_tokens = hypothesis.lower().split()
    if not hyp_tokens or not ref_tokens:
        return 0.0
    return sentence_bleu([ref_tokens], hyp_tokens, smoothing_function=_smoothing)


def calc_rouge_l(reference: str, hypothesis: str) -> float:
    """ROUGE-L F1 score."""
    scores = _rouge.score(reference, hypothesis)
    return scores["rougeL"].fmeasure


def calc_exact_match(reference: str, hypothesis: str) -> bool:
    """True if the ground-truth key content appears in the response (case-insensitive)."""
    return reference.strip().lower() in hypothesis.strip().lower()


# ---------------------------------------------------------------------------
# LLM-as-judge  (calls Ollama directly so the backend doesn't need changes)
# ---------------------------------------------------------------------------
JUDGE_PROMPT = """You are an impartial evaluator. A student asked a question about South Eastern University of Sri Lanka (SEUSL).

Question: {question}

Reference (ground-truth) answer:
{ground_truth}

Chatbot response:
{response}

Rate the chatbot response on a scale of 1-5:
1 = Completely wrong or irrelevant
2 = Partially relevant but mostly incorrect or missing key facts
3 = Somewhat correct but missing important details
4 = Mostly correct with minor omissions or inaccuracies
5 = Fully correct and complete

Reply with ONLY a single integer (1-5) and nothing else."""


def llm_judge_score(question: str, ground_truth: str, response: str) -> int | None:
    """Ask the local LLM to rate the response 1-5. Returns None on failure."""
    prompt = JUDGE_PROMPT.format(
        question=question,
        ground_truth=ground_truth,
        response=response,
    )
    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": JUDGE_MODEL, "prompt": prompt, "stream": False},
            timeout=120,
        )
        resp.raise_for_status()
        text = resp.json().get("response", "").strip()
        # Extract the first digit found
        for ch in text:
            if ch.isdigit() and 1 <= int(ch) <= 5:
                return int(ch)
        return None
    except Exception as exc:
        print(f"    [judge error] {exc}")
        return None


# ---------------------------------------------------------------------------
# Main evaluation loop
# ---------------------------------------------------------------------------

def run_evaluation(
    dataset_path: Path,
    base_url: str,
    use_llm_judge: bool,
    output_path: Path,
):
    with open(dataset_path, encoding="utf-8") as f:
        dataset = json.load(f)

    total = len(dataset)
    print(f"Loaded {total} test questions from {dataset_path.name}\n")

    chat_url = f"{base_url.rstrip('/')}/chat"

    # Verify backend is reachable
    try:
        r = requests.get(f"{base_url.rstrip('/')}/", timeout=10)
        r.raise_for_status()
        print(f"Backend OK: {r.json()}\n")
    except Exception as exc:
        print(f"ERROR: Cannot reach backend at {base_url} — {exc}")
        print("Start the backend first:  uvicorn app:app --reload")
        sys.exit(1)

    results = []
    bleu_scores = []
    rouge_scores = []
    exact_matches = 0
    judge_scores = []

    for i, item in enumerate(dataset, 1):
        qid = item["id"]
        question = item["question"]
        ground_truth = item["ground_truth"]
        category = item.get("category", "")

        print(f"[{i}/{total}] Q{qid} ({category}): {question[:80]}...")

        # Send to chatbot
        try:
            resp = requests.post(
                chat_url,
                json={"message": question, "language": "en"},
                timeout=120,
            )
            resp.raise_for_status()
            data = resp.json()
            response_text = data.get("response", "")
            sources = data.get("sources", [])
        except Exception as exc:
            print(f"    [request error] {exc}")
            response_text = ""
            sources = []

        # Calculate metrics
        bleu = calc_bleu(ground_truth, response_text)
        rouge_l = calc_rouge_l(ground_truth, response_text)
        exact = calc_exact_match(ground_truth, response_text)

        bleu_scores.append(bleu)
        rouge_scores.append(rouge_l)
        if exact:
            exact_matches += 1

        judge = None
        if use_llm_judge and response_text:
            judge = llm_judge_score(question, ground_truth, response_text)
            if judge is not None:
                judge_scores.append(judge)

        result_entry = {
            "id": qid,
            "category": category,
            "question": question,
            "ground_truth": ground_truth,
            "response": response_text,
            "sources": sources,
            "metrics": {
                "bleu": round(bleu, 4),
                "rouge_l": round(rouge_l, 4),
                "exact_match": exact,
            },
        }
        if use_llm_judge:
            result_entry["metrics"]["llm_judge"] = judge

        results.append(result_entry)

        print(f"    BLEU={bleu:.4f}  ROUGE-L={rouge_l:.4f}  Exact={exact}"
              + (f"  Judge={judge}" if use_llm_judge else ""))

    # ---------------------------------------------------------------------------
    # Aggregate summary
    # ---------------------------------------------------------------------------
    avg_bleu = sum(bleu_scores) / len(bleu_scores) if bleu_scores else 0
    avg_rouge = sum(rouge_scores) / len(rouge_scores) if rouge_scores else 0
    exact_pct = (exact_matches / total * 100) if total else 0
    avg_judge = (sum(judge_scores) / len(judge_scores)) if judge_scores else None

    # Per-category breakdown
    categories = sorted(set(item.get("category", "") for item in dataset))
    category_stats = {}
    for cat in categories:
        cat_results = [r for r in results if r["category"] == cat]
        cat_bleu = [r["metrics"]["bleu"] for r in cat_results]
        cat_rouge = [r["metrics"]["rouge_l"] for r in cat_results]
        cat_exact = sum(1 for r in cat_results if r["metrics"]["exact_match"])
        cat_judge = [r["metrics"].get("llm_judge") for r in cat_results
                     if r["metrics"].get("llm_judge") is not None]
        category_stats[cat] = {
            "count": len(cat_results),
            "avg_bleu": round(sum(cat_bleu) / len(cat_bleu), 4) if cat_bleu else 0,
            "avg_rouge_l": round(sum(cat_rouge) / len(cat_rouge), 4) if cat_rouge else 0,
            "exact_match_pct": round(cat_exact / len(cat_results) * 100, 2) if cat_results else 0,
        }
        if cat_judge:
            category_stats[cat]["avg_llm_judge"] = round(sum(cat_judge) / len(cat_judge), 2)

    summary = {
        "total_questions": total,
        "avg_bleu": round(avg_bleu, 4),
        "avg_rouge_l": round(avg_rouge, 4),
        "exact_match_pct": round(exact_pct, 2),
        "by_category": category_stats,
    }
    if avg_judge is not None:
        summary["avg_llm_judge"] = round(avg_judge, 2)

    output = {"summary": summary, "results": results}

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 60)
    print("EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Total questions : {total}")
    print(f"  Avg BLEU        : {avg_bleu:.4f}")
    print(f"  Avg ROUGE-L     : {avg_rouge:.4f}")
    print(f"  Exact Match     : {exact_matches}/{total} ({exact_pct:.1f}%)")
    if avg_judge is not None:
        print(f"  Avg LLM Judge   : {avg_judge:.2f} / 5.0  ({len(judge_scores)} rated)")
    print(f"\n  Results saved to: {output_path}")

    print("\n  Per-category breakdown:")
    for cat, stats in category_stats.items():
        line = (f"    {cat:20s}  n={stats['count']:3d}  "
                f"BLEU={stats['avg_bleu']:.4f}  "
                f"ROUGE-L={stats['avg_rouge_l']:.4f}  "
                f"Exact={stats['exact_match_pct']:5.1f}%")
        if "avg_llm_judge" in stats:
            line += f"  Judge={stats['avg_llm_judge']:.2f}"
        print(line)
    print("=" * 60)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Evaluate SEUSL SmartBot")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET,
                        help="Path to test_dataset.json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="Path for JSON results output")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL,
                        help="Base URL of the FastAPI backend")
    parser.add_argument("--no-llm-judge", action="store_true",
                        help="Skip the LLM-as-judge scoring (faster)")
    args = parser.parse_args()

    run_evaluation(
        dataset_path=args.dataset,
        base_url=args.base_url,
        use_llm_judge=not args.no_llm_judge,
        output_path=args.output,
    )


if __name__ == "__main__":
    main()
