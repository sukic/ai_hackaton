import json
import os
from openai import OpenAI

def generate_report_data():
    # --- načteme původní data ---
    with open("summary_output.json", "r", encoding="utf-8") as f:
        summary_data = json.load(f)

    # --- připravíme prompt pro textové shrnutí ---
    prompt = f"""
    Mám JSON výstup z validace AI systému pro přirozený dotaz → SQL.

    Úkolem je:
    - Vypracovat stručné textové hodnocení výsledků
    - Zahrnout celkovou úspěšnost, datovou shodu, silné a slabé stránky
    - Doporučit oblasti ke zlepšení
    - Srozumitelně pro netechnického člověka

    Výstup vrať jako JSON objekt:
    {{
        "celkova_uspesnost": "text",
        "datova_shoda": "text",
        "silne_slabe_stranky": "text",
        "doporuceni": "text"
    }}

    Zde je vstupní JSON ke zpracování:
    """ + str(summary_data)

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={ "type": "json_object" },
        messages=[
            {"role": "system", "content": "Jsi užitečný asistent. Piš pouze JSON výstup."},
            {"role": "user", "content": prompt}
        ],
        temperature=0
    )
    #summary_texts = json.loads(resp.choices[0].message.content)
    # raw_content obsahuje obsah odpovědi od modelu
    raw_content = resp.choices[0].message.content.strip()

    try:
        # 1) zkusíme rovnou načíst JSON
        summary_texts = json.loads(raw_content)
    except json.JSONDecodeError:
        # 2) pokud selže, najdeme první { a poslední }
        start = raw_content.find("{")
        end = raw_content.rfind("}") + 1
        if start == -1 or end == -1:
            raise ValueError("Neplatný výstup od modelu, JSON nenalezen")
        summary_texts = json.loads(raw_content[start:end])

    # --- připojíme do původního JSONu ---
    summary_data["summary"] = summary_texts

    # --- uložíme obohacený JSON ---
    with open("summary_output_enriched.json", "w", encoding="utf-8") as f:
        json.dump(summary_data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    generate_report_data()
