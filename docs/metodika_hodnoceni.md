# Procento shody dat (data_match_score)

Cílem je vyjádřit, **jak moc se obsah tabulek AI a Control shoduje**, nezávisle na tom, že struktura (sloupce/řádky) už sedí.  

## 1. Princip

- Rozdělíme sloupce na **číselné** a **textové**.  
- Pro každý sloupec spočítáme **lokální skóre** 0–100 %.  
- Potom vezmeme **průměr přes všechny sloupce** a dostaneme celkové `data_match_score`.  

## 2. Číselné sloupce

- Používáme základní statistiky: `min, Q1, median, Q3, max, avg`.  
- Pro každou statistiku spočítáme relativní rozdíl:  

\[
\text{diff} = \frac{|ai - control|}{control}
\]

- Z těchto rozdílů uděláme **průměrný rozdíl** a odečteme od 100 %:  

\[
\text{score} = 100 - (\text{průměrný rozdíl} \times 100)
\]

- Hodnoty blízko 100 % → téměř stejné, nízké → velké rozdíly.  

## 3. Textové sloupce

- Používáme **overlap_ratio**, tedy podíl hodnot AI, které se shodují s Control:  

\[
\text{score} = \text{overlap\_ratio} \times 100
\]

- overlap_ratio = 1 → 100 % shoda  
- overlap_ratio = 0.7 → 70 % shoda  

## 4. Celkové skóre

- Vezmeme **průměr všech sloupců** (číselné i textové).  
- Výsledek je `data_match_score` v rozsahu 0–100 %, snadno porovnatelný mezi jednotlivými prompt ID.  

## 5. Shrnutí

- **Struktura** → shoda sloupců a řádků (True/False)  
- **Obsah** → `data_match_score` (0–100 %)  
  - Číselné sloupce → relativní rozdíly statistických hodnot  
  - Textové sloupce → overlap unikátních hodnot  
- **Celkové skóre** → průměr přes všechny sloupce
