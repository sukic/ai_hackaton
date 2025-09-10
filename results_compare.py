import os
import json
import statistics
from collections import defaultdict

DATA_DIR = "results"  # složka se všemi JSONy

# # === Nastavení filtru operations ===
# # jen dotazy, kde je přesně join
# OPERATIONS_FILTER = lambda ops: ops == ["join"]

# # jen dotazy, kde se vyskytuje filter_dim
# OPERATIONS_FILTER = lambda ops: "filter_dim" in ops

# # všechny dotazy (bez filtru)
# OPERATIONS_FILTER = lambda ops: True


OPERATIONS_FILTER = lambda ops: True #vsechny dotazy bez filtru


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def parse_filename(filename):
    # očekáváme formát: prompt_sql_results-idX-type.json
    parts = filename.replace(".json", "").split("-")
    return parts[1], parts[2]  # (id, prompt_type)

def compare_data(ai_data, ctrl_data):
    # základní kontrola: stejné hodnoty
    return ai_data == ctrl_data

def main():
    files = os.listdir(DATA_DIR)

    # uspořádáme podle ID
    grouped = defaultdict(dict)
    for filename in files:
        if not filename.endswith(".json"):
            continue
        path = os.path.join(DATA_DIR, filename)
        qid, ptype = parse_filename(filename)
        grouped[qid][ptype] = load_json(path)

    results = []
    categories = defaultdict(list)

    for qid, variants in grouped.items():
        if "control" not in variants:
            continue  # bez kontrolního dotazu nemůžeme porovnávat
        ctrl = variants["control"]

        for ptype, ai_json in variants.items():
            if ptype == "control":
                continue

            # === filtr podle operations ===
            ai_ops = ai_json["meta"].get("operations", [])
            if not OPERATIONS_FILTER(ai_ops):
                continue

            ai_duration = ai_json["meta"]["duration"]
            ctrl_duration = ctrl["meta"]["duration"]

            correct = compare_data(ai_json["results"]["data"], ctrl["results"]["data"])
            faster = ai_duration < ctrl_duration if correct else False

            results.append({
                "qid": qid,
                "prompt_type": ptype,
                "correct": correct,
                "ai_duration": ai_duration,
                "ctrl_duration": ctrl_duration,
                "faster": faster,
                "operations": ai_ops
            })

            categories[ptype].append(correct)

    # === Report ===
    total = len(results)
    if total == 0:
        print("⚠️ Žádné výsledky po aplikaci filtru operations.")
        return

    correct_total = sum(r["correct"] for r in results)
    print(f"Celková úspěšnost: {correct_total}/{total} ({correct_total/total:.0%})")

    print("\nPo kategoriích:")
    for cat, vals in categories.items():
        acc = sum(vals) / len(vals)
        print(f" - {cat}: {acc:.0%}")

    if results:
        avg_ai = statistics.mean(r["ai_duration"] for r in results)
        avg_ctrl = statistics.mean(r["ctrl_duration"] for r in results)
        print(f"\nPrůměrná doba běhu AI: {avg_ai:.2f}s vs Control: {avg_ctrl:.2f}s")

if __name__ == "__main__":
    main()
