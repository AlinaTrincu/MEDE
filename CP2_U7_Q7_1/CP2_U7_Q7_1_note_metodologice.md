# CP2 · U7 / Q7.1 — Trăsături și PCA

## Rezumatul rezultatului

Matricea completă conține **162.397 observații lac–lună × 5 trăsături**, provenite din **647 lacuri**. Selecția inițială conține 1.111 lacuri și 278.861 rânduri, dar 116.464 rânduri nu au temperatura și precipitația ERA5-Land; acestea rămân lipsă și sunt excluse din X completă. Exportul acoperă 251 luni, ianuarie 2001–noiembrie 2021. Decembrie 2021 lipsește.

PCA standardizată cu parametri ajustați numai pe train (2001–2017) explică **40,4%** din variație cu PC1 și **61,6%** cu PC1–PC2. Pe testul temporal (2018–noiembrie 2021), eroarea RMSE de reconstrucție pentru k=2 este **0,620 deviații standard** per valoare standardizată. Acesta este un rezultat de bază; nu arată că două componente sunt suficiente pentru toate scopurile.

## Aliniere și construirea lui X

- Unitatea unui rând: Hylak_id × YYYY-MM (lac × lună calendaristică).
- Fereastra declarată: 2001-01–2021-12; fișierul efectiv se termină la 2021-11.
- Spațial: JRC Global Surface Water Monthly History v1.4 este agregat ca arie de pixeli din clasa apă (clasa 2) în poligonul HydroLAKES, la 30 m. valid_area_km2 înregistrează acoperirea JRC și servește ca diagnostic.
- ERA5-Land Monthly Aggregated este extras prin reduceRegions peste același poligon, reducer mean, la scară 11.132 m. Scriptul nu reproiectează rasterul și nu interpolă; media la rezoluția sursei este transferată la unitatea lac–lună.
- Temporal: fiecare colecție lunară este asociată la aceeași lună calendaristică. Nu se aplică lag și nu se agregă la alt pas.
- Semantica și unitățile: temperature_2m este convertită K → °C; precipitația lunară totală este convertită m → mm; aria JRC este m² → km²; month_sin și month_cos codifică ciclic luna.
- Nu se impută lipsuri. Rândurile fără valori complete pentru cele cinci trăsături nu intră în X și sunt contabilizate în raportul de acoperire. valid_area_km2 nu intră în PCA.
- Limită de documentare: fișa CP1 descrie media ERA5 drept medie pe poligon. Codul face reduceRegions peste poligon la scara de 11.132 m; descrierea corectă este media pixelilor ERA5 intersectați cu fiecare poligon, nu eșantionare la centroid.

## Dicționarul matricei X

| Grup | Trăsătură | Sursă / transformare | Unitate | Observație |
|---|---|---|---|---|
| Optic | water_km2 | JRC GSW v1.4, suma pixelilor clasificați apă în poligon | km² | Arie observată lunar |
| Climă | t2m_c | ERA5-Land, media lunară temperature_2m, Kelvin convertit | °C | Media pixelilor din poligon |
| Climă | precip_mm | ERA5-Land, total lunar convertit | mm/lună | Total lunar |
| Calendar | month_sin | sin(2π × luna / 12) | adimensională | Componentă ciclică |
| Calendar | month_cos | cos(2π × luna / 12) | adimensională | Componentă ciclică |

Matricea X pentru PCA: **n=162.397**, **d=5**. Cheile Hylak_id, month, year, month_number rămân metadata, nu predictori PCA.

## Statistici descriptive pe X completă

| Trăsătură | Medie | Mediană | Q1–Q3 | Deviație standard | Asimetrie |
|---|---:|---:|---:|---:|---:|
| water_km2 | 1,598 | 0,033 | 0–0,475 | 16,366 | 26,86 |
| t2m_c | 11,62 | 11,54 | 3,93–19,53 | 8,75 | −0,07 |
| precip_mm | 53,12 | 46,49 | 27,49–69,87 | 35,40 | 1,44 |
| month_sin | 0,000 | 0,000 | −0,866–0,866 | 0,709 | ~0 |
| month_cos | −0,004 | ~0 | −0,866–0,500 | 0,706 | 0,006 |

Distribuția ariei este puternic asimetrică, iar 45,7% dintre rândurile complete au water_km2=0. Rezultatele PCA trebuie interpretate ținând cont de coada lungă; o analiză robustă sau log1p(water_km2) este o verificare ulterioară, nu rezultatul prezentat aici.

## Corelații Pearson

| Pereche | r |
|---|---:|
| Arie JRC – temperatură ERA5-Land | 0,062 |
| Arie JRC – precipitație ERA5-Land | −0,007 |
| Temperatură – precipitație ERA5-Land | 0,090 |
| Temperatură – month_sin | −0,523 |
| Temperatură – month_cos | −0,805 |

În exportul curent, corelațiile simple arie–climă sunt mici. Acestea descriu asocierea liniară pe rândurile complete și nu demonstrează cauzalitate; structura pe lac și sezonalitatea pot influența rezultatul.

## PCA și protocol

- Scalare: StandardScaler; media și deviația standard sunt estimate numai pe train, apoi aplicate testului.
- Split temporal: train 2001–2017 (**131.988 × 5**); test 2018–2021-11 (**30.409 × 5**).
- PCA: sklearn.decomposition.PCA(svd_solver="full"); algoritm determinist, seed-uri nerelevante.
- Baseline: PCA liniară pe toate cele cinci trăsături scalate. Alternativă declarată pentru etapele următoare: UMAP; în CP2 nu este evaluată.

| Componentă | Varianță explicată individual | Cumulat |
|---|---:|---:|
| PC1 | 40,36% | 40,36% |
| PC2 | 21,27% | 61,63% |
| PC3 | 20,03% | 81,66% |
| PC4 | 17,69% | 99,35% |
| PC5 | 0,65% | 100,00% |

Loadings principale:

| Trăsătură | PC1 | PC2 |
|---|---:|---:|
| water_km2 | 0,080 | −0,015 |
| t2m_c | 0,681 | −0,138 |
| precip_mm | 0,218 | 0,593 |
| month_sin | −0,356 | 0,705 |
| month_cos | −0,596 | −0,364 |

Metrică pe test: RMSE de reconstrucție în spațiul standardizat este 0,800 (k=1), 0,620 (k=2), 0,409 (k=3) și 0,080 (k=4). Pentru k=2, train cumulează 61,63% varianță explicată, iar eroarea test este 0,620 SD.

## Fișiere reproductibile

- Script analiză: cp2_analysis.py
- Figura compozită: CP2_U7_Q7_1_support/CP2_evidence_figure.png
- Dicționar: feature_dictionary.csv
- Statistici: descriptive_statistics.csv
- Corelații: correlation_matrix.csv
- Loadings: pca_loadings.csv
- Metrici PCA train/test: pca_temporal_metrics.csv
- Rezumat acoperire: cp2_dataset_summary.csv
- Cod GEE CP1: pipeline_U7_Q7_1_actualizat.js
- Repo proiect: https://github.com/AlinaTrincu/MEDE
