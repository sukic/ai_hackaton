import os
import json
import statistics
import numpy as np
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

def numeric_stats(values):
    nums = [float(v) for v in values if isinstance(v, (int, float))]
    if not nums:
        return None
    
    return {
        "count": len(nums),
        "min": min(nums),
        "q1": float(np.percentile(nums, 25)),
        "median": statistics.median(nums),
        "q3": float(np.percentile(nums, 75)),
        "max": max(nums),
        "avg": statistics.mean(nums),
        "std": statistics.pstdev(nums) if len(nums) > 1 else 0.0
    }

def text_stats(ai_values, ctrl_values):
    ai_set = set(str(v) for v in ai_values if v not in (None, ""))
    ctrl_set = set(str(v) for v in ctrl_values if v not in (None, ""))
    if not ai_set or not ctrl_set:
        return None
    
    overlap = ai_set & ctrl_set
    overlap_ratio = len(overlap) / max(len(ctrl_set), 1)
    
    return {
        "ai_unique": len(ai_set),
        "ctrl_unique": len(ctrl_set),
        "overlap_ratio": overlap_ratio
    }


def compare_data(ai_data, ctrl_data):
    # === 1. základní kontrola ===
    if not ai_data or not ctrl_data:
        return {"same_columns": False, "same_rowcount": False, "columns": {}, "rowcount_ai": len(ai_data), "rowcount_ctrl": len(ctrl_data)}
    
    ai_cols = set(ai_data[0].keys())
    ctrl_cols = set(ctrl_data[0].keys())
    same_columns = ai_cols == ctrl_cols
    same_rowcount = len(ai_data) == len(ctrl_data)
    
    results = {
        "same_columns": same_columns,
        "same_rowcount": same_rowcount,
        "rowcount_ai": len(ai_data),
        "rowcount_ctrl": len(ctrl_data),
        "columns": {}
    }
    
    # === 2. detailní srovnání po sloupcích ===
    for col in ai_cols & ctrl_cols:
        ai_values = [row[col] for row in ai_data if col in row]
        ctrl_values = [row[col] for row in ctrl_data if col in row]
        
        # Zkusíme převést na čísla
        ai_nums = []
        ctrl_nums = []
        numeric = True
        for v in ai_values:
            try:
                ai_nums.append(float(v))
            except:
                numeric = False
                break
        for v in ctrl_values:
            try:
                ctrl_nums.append(float(v))
            except:
                numeric = False
                break
        
        if numeric:
            stats = {
                "ai": numeric_stats(ai_nums),
                "ctrl": numeric_stats(ctrl_nums)
            }
        else:
            stats = text_stats(ai_values, ctrl_values)
        
        results["columns"][col] = stats
    
    return results

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

            comparison = compare_data(ai_json["results"]["data"], ctrl["results"]["data"])
            correct = comparison["same_columns"] and comparison["same_rowcount"]

            results.append({
                "qid": qid,
                "prompt_type": ptype,
                "correct": correct,
                "ai_duration": ai_duration,
                "ctrl_duration": ctrl_duration,
                "faster": faster,
                "operations": ai_ops,
                "details": comparison
            })

            categories[ptype].append(correct)

    # === Report ===
    total = len(results)
    if total == 0:
        print("⚠️ Žádné výsledky po aplikaci filtru operations.")
        return

    # --- 1️⃣ Shoda struktury ---
    correct_total = sum(r["correct"] for r in results)
    print(f"Celková úspěšnost (struktura): {correct_total}/{total} ({correct_total/total:.0%})")

    print("\nPo kategoriích (struktura):")
    for cat, vals in categories.items():
        acc = sum(vals) / len(vals)
        print(f" - {cat}: {acc:.0%}")

    if results:
        avg_ai = statistics.mean(r["ai_duration"] for r in results)
        avg_ctrl = statistics.mean(r["ctrl_duration"] for r in results)
        print(f"\nPrůměrná doba běhu AI: {avg_ai:.2f}s vs Control: {avg_ctrl:.2f}s")

    # --- 2️⃣ Statistická analýza (detaily z compare_data) ---
    print("\nStatistická analýza (detaily sloupců):")
    for r in results:
        print(f"\nQID: {r['qid']} | Prompt type: {r['prompt_type']}")
        for col, stats in r["details"]["columns"].items():
            print(f"  Sloupec: {col}")
            if stats is None:
                print("    (žádné hodnoty)")
                continue
            if "ai" in stats and stats["ai"] is not None:  # číselné
                print(f"    AI: {stats['ai']}")
                print(f"    Control: {stats['ctrl']}")
            else:  # textové
                print(f"    Text stats: {stats}")


if __name__ == "__main__":
    main()
