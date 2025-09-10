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
    rowcount_ai = len(ai_data)
    rowcount_ctrl = len(ctrl_data)
    if not ai_data or not ctrl_data:
        return {
            "same_columns": False,
            "same_rowcount": False,
            "rowcount_ai": rowcount_ai,
            "rowcount_ctrl": rowcount_ctrl,
            "columns": {}
        }
    
    ai_cols = set(ai_data[0].keys())
    ctrl_cols = set(ctrl_data[0].keys())
    same_columns = ai_cols == ctrl_cols
    same_rowcount = rowcount_ai == rowcount_ctrl
    
    results = {
        "same_columns": same_columns,
        "same_rowcount": same_rowcount,
        "rowcount_ai": rowcount_ai,
        "rowcount_ctrl": rowcount_ctrl,
        "columns": {}
    }
    
    # === 2. detailní srovnání po sloupcích ===
    for col in ai_cols & ctrl_cols:
        ai_values = [row[col] for row in ai_data if col in row]
        ctrl_values = [row[col] for row in ctrl_data if col in row]
        
        # pokus převést na čísla
        numeric = True
        ai_nums, ctrl_nums = [], []
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

def compute_data_match_score(details):
    """
    Vrátí procento shody dat mezi AI a Control.
    - Číselné sloupce: 100% pokud min, max, median, avg jsou velmi blízko, jinak sníženo podle rozdílu
    - Textové sloupce: overlap_ratio * 100
    """
    if not details or "columns" not in details:
        return 0.0

    scores = []
    for col, stats in details["columns"].items():
        if stats is None:
            continue
        # číselné
        if "ai" in stats and stats["ai"] is not None:
            ai_vals = stats["ai"]
            ctrl_vals = stats["ctrl"]
            # jednoduchý přístup: průměrný rozdíl v %
            diffs = []
            for key in ["min", "q1", "median", "q3", "max", "avg"]:
                if key in ai_vals and key in ctrl_vals and ctrl_vals[key] != 0:
                    diffs.append(abs(ai_vals[key] - ctrl_vals[key]) / ctrl_vals[key])
            score = max(0, 100 - (sum(diffs)/len(diffs)*100)) if diffs else 100
        else:  # textové
            score = stats.get("overlap_ratio", 0.0) * 100
        scores.append(score)
    
    return sum(scores)/len(scores) if scores else 0.0

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

    # === Report a detailní výstup do JSON ===
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

    # --- 2️⃣ Průměrná doba běhu ---
    if results:
        avg_ai = statistics.mean(r["ai_duration"] for r in results)
        avg_ctrl = statistics.mean(r["ctrl_duration"] for r in results)
        print(f"\nPrůměrná doba běhu AI: {avg_ai:.5f}s vs Control: {avg_ctrl:.5f}s")

    # --- 3️⃣ Výpočet data_match_score a uložení detailů do JSON ---
    details_output = {}
    mismatch_ids = []

    for r in results:
        qid_type = f"{r['qid']}-{r['prompt_type']}"
        data_score = compute_data_match_score(r["details"])
        
        # uložíme detaily + data_match_score
        details_output[qid_type] = {**r["details"], "data_match_score": data_score}
        
        if not r["correct"]:
            mismatch_ids.append(qid_type)

    # uložíme do souboru
    with open("results_details.json", "w", encoding="utf-8") as f:
        json.dump(details_output, f, indent=2, ensure_ascii=False)

    # --- souhrnný report pro JSON ---
    avg_data_score = sum(d["data_match_score"] for d in details_output.values()) / len(details_output)
    sorted_scores = sorted(details_output.items(), key=lambda x: x[1]["data_match_score"], reverse=True)

    summary_json = {
        "total_prompts": total,
        "correct_total": correct_total,
        "correct_percentage": correct_total / total * 100 if total else 0,
        "avg_ai_duration": avg_ai,
        "avg_ctrl_duration": avg_ctrl,
        "categories": {cat: sum(vals)/len(vals) for cat, vals in categories.items()},
        "data_match": {
            "average_score": avg_data_score,
            "top5_best": [{"id": qid, "score": det["data_match_score"]} for qid, det in sorted_scores[:5]],
            "top5_worst": [{"id": qid, "score": det["data_match_score"]} for qid, det in sorted_scores[-5:]],
            "mismatch_ids": mismatch_ids
        }
    }

    # --- uložíme souhrnný report ---
    with open("summary_output.json", "w", encoding="utf-8") as f:
        json.dump(summary_json, f, indent=2, ensure_ascii=False)
    
    
    
    # --- 4️⃣ Souhrnný report do stdout ---
    print("\nCelková statistika datové shody:")
    avg_score = sum(d["data_match_score"] for d in details_output.values()) / len(details_output)
    print(f"Průměrná shoda dat: {avg_score:.1f}%")

    # TOP 5 nejlepších a nejhorších
    sorted_scores = sorted(details_output.items(), key=lambda x: x[1]["data_match_score"], reverse=True)
    print("\nTOP 5 nejlepších ID:")
    for qid, det in sorted_scores[:5]:
        print(f"  {qid}: {det['data_match_score']:.1f}%")
    print("\nTOP 5 nejhorších ID:")
    for qid, det in sorted_scores[-5:]:
        print(f"  {qid}: {det['data_match_score']:.1f}%")

    # ID s nesedící strukturou
    if mismatch_ids:
        print("\nID s nesedící strukturou (sloupce/řádky):")
        for qid in mismatch_ids:
            print(f"  {qid}")



if __name__ == "__main__":
    main()
