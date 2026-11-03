# MEDE CP2 · U7 / Q7.1

Analiza exploratorie a regimurilor sezoniere ale suprafeței lacurilor din România. Unitatea de analiză este lac × lună.

## Conținut

- scripts/pipeline_U7_Q7_1.js: pipeline-ul Google Earth Engine pentru alinierea JRC, ERA5-Land și HydroLAKES și exportul în Google Drive.
- data/U7_Q7_1_lac_luna_2001_2021.csv.gz: snapshot-ul CSV folosit pentru rezultatele CP2, comprimat.
- scripts/cp2_analysis.py: reconstruiește statistici descriptive, corelații, PCA, loadings, metrici de test și figura din slide.
- results/: ieșirile generate de script.
- CP2_Trincu.pdf: checkpoint-ul CP2.
- CP2_U7_Q7_1_note_metodologice.md: descrierea alinierii, trăsăturilor și interpretarea rezultatelor.

## Rulare pe Windows

Instalează Python 3.10 sau mai nou. Deschide PowerShell în folderul proiectului și rulează, pe rând:

    py -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    .\.venv\Scripts\python.exe scripts\cp2_analysis.py

Scriptul citește CSV-ul comprimat din data/ și regenerează fișierele din results/. Nu trebuie să dezarhivezi CSV-ul.

Pentru a regenera datele din surse, deschide scripts/pipeline_U7_Q7_1.js în Google Earth Engine Code Editor, rulează scriptul și descarcă exportul din Google Drive. Păstrează CSV-ul brut și rulează analiza Python separat. Exportul inclus aici se termină în noiembrie 2021; decembrie 2021 lipsește. Scriptul nu completează automat luna lipsă.

## Reproducibilitate și limitări

- Split temporal: train 2001–2017, test 2018–noiembrie 2021.
- StandardScaler se ajustează numai pe train; aceiași parametri se aplică pe test.
- PCA folosește svd_solver="full", deci nu are seed aleator.
- Lipsurile ERA5-Land nu se impută. X completă conține 162.397 rânduri × 5 trăsături din 647 lacuri.
- Corelațiile sunt descriptive și nu demonstrează cauzalitate.
- valid_area_km2 rămâne câmp de diagnostic JRC, nu intră în PCA.
