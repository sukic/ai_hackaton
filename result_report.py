from openai import OpenAI
import json
import os

with open("summary_output.json", "r", encoding="utf-8") as f:
    summary_data = json.load(f)

prompt = f"""
Mám JSON výstup z validace AI systému pro přirozený dotaz → SQL. JSON obsahuje shrnutí úspěšnosti a podrobné statistiky pro jednotlivé prompty.

Úkolem je:
- Vypracovat stručné textové hodnocení výsledků
- Zahrnout celkovou úspěšnost, datovou shodu, silné a slabé stránky
- Doporučit oblasti ke zlepšení
- Srozumitelně pro netechnického člověka
- Výstup připojit k původnímu JSON souboru, jako nový objekt "summary" v podobě
"summary": {{
        "celkova_uspesnost": "",
        "datova_shoda": "",
        "silne_slabe_stranky": "",
        "doporuceni": ""
        }}
- v každém tom objektu ze "summary" je prostý text 1 - 2 odstavce
- vystupem je pouze ten obohaceny JSON, nic jineho tam nesmi byt

JSON:
{json.dumps(summary_data, indent=2)}
"""

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "Jsi užitečný asistent. Tvým cílem je připravit strukturované podklady pro report v předem definovaném JSON souboru"},
        {"role": "user", "content": prompt}
    ],
    temperature=0,
    #max_tokens=500
)

print(resp.choices[0].message.content)