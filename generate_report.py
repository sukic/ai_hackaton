import json
from pathlib import Path

# ==== Konfigurace souborů ====
JSON_FILE = "summary_output_enriched.json"
HTML_FILE = "report.html"

def generate_report():
    # Načtení JSONu
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Příprava HTML
    html = f"""
<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>AI Hackaton - Datachatbot - Validace</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body {{
    font-family: Arial, sans-serif;
    margin: 20px;
    max-width: 900px;  /* omezíme celou stránku */
    margin-left: auto;
    margin-right: auto;
}}
header {{
    display: flex;
    align-items: center;
    height: 100px;
    border-bottom: 1px solid #ccc;
    margin-bottom: 20px;
}}
header img {{
    height: 80px;
    margin-right: 20px;
}}
section {{
    margin-bottom: 30px;
}}
h2 {{
    border-bottom: 1px solid #eee;
    padding-bottom: 5px;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin-top: 10px;
}}
table, th, td {{
    border: 1px solid #ccc;
}}
th, td {{
    padding: 5px;
    text-align: left;
}}
canvas {{
    max-width: 100%;   /* graf se přizpůsobí šířce kontejneru */
    height: 300px;     /* zmenšená výška */
}}
</style>
</head>
<body>
<header>
    <img src="logo_cm.png" alt="Logo">
    <h1>AI Hackaton - Datachatbot - Validace</h1>
</header>

<section>
<h2>Textové shrnutí</h2>
<p><b>Celková úspěšnost:</b> {data["correct_percentage"]:.2f}% ({data["correct_total"]}/{data["total_prompts"]})</p>
<p><b>Průměrná doba běhu AI:</b> {data["avg_ai_duration"]*1000:.3f} ms</p>
<p><b>Průměrná doba běhu Control:</b> {data["avg_ctrl_duration"]*1000:.3f} ms</p>

<p><b>Celkova úspěšnost (summary):</b> {data["summary"]["celkova_uspesnost"]}</p>
<p><b>Datová shoda:</b> {data["summary"]["datova_shoda"]}</p>
<p><b>Silné a slabé stránky:</b> {data["summary"]["silne_slabe_stranky"]}</p>
<p><b>Doporučení:</b> {data["summary"]["doporuceni"]}</p>
</section>

<section>
<h2>Kategorie úspěšnosti</h2>
<canvas id="categoriesChart"></canvas>
<script>
const ctx = document.getElementById('categoriesChart').getContext('2d');
new Chart(ctx, {{
    type: 'bar',
    data: {{
        labels: {list(data["categories"].keys())},
        datasets: [{{
            label: 'Úspěšnost po kategoriích',
            data: {list(data["categories"].values())},
            backgroundColor: 'rgba(54, 162, 235, 0.7)'
        }}]
    }},
    options: {{
        scales: {{
            y: {{
                beginAtZero: true,
                max: 1
            }}
        }}
    }}
}});
</script>
</section>

<section>
<h2>Datová shoda</h2>
<p><b>Průměrná datová shoda:</b> {data["data_match"]["average_score"]:.2f}%</p>

<h3>Top 5 nejlepší</h3>
<table>
<tr><th>ID</th><th>Skóre (%)</th></tr>
{''.join(f"<tr><td>{item['id']}</td><td>{item['score']}</td></tr>" for item in data["data_match"]["top5_best"])}
</table>

<h3>Top 5 nejhorší</h3>
<table>
<tr><th>ID</th><th>Skóre (%)</th></tr>
{''.join(f"<tr><td>{item['id']}</td><td>{item['score']}</td></tr>" for item in data["data_match"]["top5_worst"])}
</table>

<h3>Chybné ID (mismatch)</h3>
<ul>
{''.join(f"<li>{mid}</li>" for mid in data["data_match"]["mismatch_ids"])}
</ul>
</section>

</body>
</html>
"""

    # Uložení do souboru
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML report vygenerován: {HTML_FILE}")

if __name__ == "__main__":
    generate_report()
