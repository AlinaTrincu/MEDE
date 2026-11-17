# CP3 U7/Q7.1 — PCA baseline și protocol UMAP

Acest folder conține prezentarea CP3, notebook-ul Colab, scriptul de analiză și rezultatele rulate pe datele proiectului. Repo: https://github.com/AlinaTrincu/MEDE

## Conținut

- `CP3_U7_Q7_1_Alina_Trincu.pdf` — varianta de predat pe Moodle.
- `CP3_U7_Q7_1_Alina_Trincu.pptx` — prezentarea editabilă.
- `CP3_U7_Q7_1_colab.ipynb` — pașii de rulare în Google Colab.
- `scripts/cp3_dimensionality.py` — codul analizei.
- `results/cp3/` — metricile CSV și embedding-urile UMAP rezultate.

## Date și protocol

Datele provin din `CP2_U7_Q7_1/data/U7_Q7_1_lac_luna_2001_2021.csv.gz`. Matricea combinată are 162.397 observații (lac × lună) și 5 trăsături. Split-ul este temporal: train 2001–2017, test 2018–noiembrie 2021. Scalarea este ajustată numai pe train.

PCA este baseline-ul; UMAP este metoda de comparație. UMAP folosește un eșantion reproductibil de maximum 10.000 rânduri de train și este evaluat pe maximum 5.000 de observații test. Au fost rulate 5 seed-uri, iar trustworthiness este raportat pentru k=5, 10 și 15. Stabilitatea pe subperioade (2001–2010 și 2011–2021) este descriptivă și calculată separat în fiecare perioadă.

JRC are o singură trăsătură numerică, deci PCA/UMAP nu oferă o reducere multivariată informativă pentru acea sursă. ERA5-Land are două trăsături; comparația ei 2D→2D este un control de vecinătate. Rezultatul principal de reducere este comparația PCA vs. UMAP pe matricea combinată 5D→2D.

## Rezultatul principal obținut

Pe eșantionul fix de test, pentru matricea combinată, trustworthiness@5 este 0,9807 pentru PCA și 0,9966 ± 0,0002 pentru UMAP (medie ± SD peste 5 seed-uri). UMAP îmbunătățește această metrică cu aproximativ 0,0159. PCA explică 61,63% din variație prin primele două componente; eroarea RMSE de reconstrucție PCA este 0,526 SD, iar eroarea inversă UMAP este 0,314 SD. Interpretarea trebuie raportată împreună cu faptul că UMAP a fost fitat pe eșantionul de train, nu pe toate observațiile.

## Fișierele de rezultate

- `cp3_metrics.csv` — PCA și UMAP pe surse și combinație, incluzând trustworthiness, varianță explicată și erori.
- `cp3_umap_stability.csv` — medie și abatere standard peste seed-uri.
- `cp3_subperiod_metrics.csv`, `cp3_subperiod_stability.csv` — verificarea pe subperioade.
- `cp3_view_definition.csv` — gruparea trăsăturilor pe surse.
- `embedding_*.csv` — coordonatele UMAP pe seed și vedere.

## Rulare

Pentru rulare locală, dependențele CP3 sunt listate în `requirements_cp3.txt`; folosește un mediu Python compatibil și execută din rădăcina repo-ului:

```powershell
python -m pip install -r CP3_U7_Q7_1/requirements_cp3.txt
python CP3_U7_Q7_1/scripts/cp3_dimensionality.py
```

Notebook-ul Colab include încărcarea arhivei sursă și descărcarea arhivei cu rezultate. Analiza folosește aceeași configurație documentată mai sus.
