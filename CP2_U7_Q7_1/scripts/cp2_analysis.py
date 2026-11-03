"""Reproducible CP2 summaries and PCA for U7/Q7.1."""
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'results'
OUT.mkdir(exist_ok=True)
df=pd.read_csv(ROOT/'data'/'U7_Q7_1_lac_luna_2001_2021.csv.gz')
features=['water_km2','t2m_c','precip_mm','month_sin','month_cos']
valid=df.dropna(subset=features).copy()
train=valid[valid.year<=2017]; test=valid[valid.year>=2018]
valid[features].describe(percentiles=[.25,.5,.75]).T.assign(skew=valid[features].skew()).to_csv(OUT/'descriptive_statistics.csv')
valid[features].corr().to_csv(OUT/'correlation_matrix.csv')
scaler=StandardScaler().fit(train[features])
ztrain=scaler.transform(train[features]); ztest=scaler.transform(test[features])
pca=PCA(svd_solver='full').fit(ztrain); evr=pca.explained_variance_ratio_
loads=pd.DataFrame(pca.components_.T,index=features,columns=[f'PC{i+1}' for i in range(5)])
loads.to_csv(OUT/'pca_loadings.csv')
metrics=[]
for k in range(1,6):
    rec=pca.transform(ztest)[:,:k]@pca.components_[:k,:]+pca.mean_
    mse=float(np.mean((ztest-rec)**2))
    metrics.append({'k':k,'train_cumulative_explained_variance':evr[:k].sum(),'test_standardized_reconstruction_mse':mse,'test_standardized_reconstruction_rmse':np.sqrt(mse)})
pd.DataFrame(metrics).to_csv(OUT/'pca_temporal_metrics.csv',index=False)
pd.DataFrame([
 ['Optic / JRC','water_km2','km²','water class area inside lake polygon'],
 ['Optic / JRC','valid_area_km2','km²','JRC coverage diagnostic, not PCA input'],
 ['Climate / ERA5-Land','t2m_c','°C','monthly mean, polygon reducer, ~11.1 km scale'],
 ['Climate / ERA5-Land','precip_mm','mm/month','monthly total, polygon reducer, ~11.1 km scale'],
 ['Calendar','month_sin','unitless','sin(2π month / 12)'],
 ['Calendar','month_cos','unitless','cos(2π month / 12)'],
],columns=['group','feature','unit','definition']).to_csv(OUT/'feature_dictionary.csv',index=False)

# One wide evidence figure groups X by source, summarizes distributions and shows correlations/PCA.
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':8})
fig,axs=plt.subplots(1,3,figsize=(15,5.8),facecolor='#f7f3ed',
                     gridspec_kw={'width_ratios':[1.48,1,1.12]})
fig.suptitle('CP2 · Matricea X și baseline-ul PCA',x=.04,y=.97,ha='left',fontsize=17,color='#1b2a41',weight='bold')
ax=axs[0]; ax.axis('off')
schema=[
 ['GRUP / SURSĂ','TRĂSĂTURĂ','UNITATE'],
 ['Optic · JRC','water_km2','km²'],
 ['Climă · ERA5-Land','t2m_c','°C'],
 ['Climă · ERA5-Land','precip_mm','mm/lună'],
 ['Calendar · derivat','month_sin','fără unitate'],
 ['Calendar · derivat','month_cos','fără unitate'],
]
t=ax.table(cellText=schema[1:],colLabels=schema[0],cellLoc='left',loc='upper center',
           colWidths=[.40,.35,.25],bbox=[0,.40,1,.55])
t.auto_set_font_size(False); t.set_fontsize(7.5)
for (r,c),cell0 in t.get_celld().items():
    cell0.set_edgecolor('#d8d1c7')
    if r==0: cell0.set_facecolor('#1b2a41'); cell0.get_text().set_color('white'); cell0.get_text().set_weight('bold')
    else: cell0.set_facecolor('#fffdf9')
ax.set_title(f'X completă · {len(valid):,} rânduri × 5 trăsături',loc='left',fontsize=10,color='#1b2a41',weight='bold')
stats=[
 f'Arie apă: mediană {valid.water_km2.median():.3f} km²; IQR {valid.water_km2.quantile(.25):.3f}–{valid.water_km2.quantile(.75):.3f}; medie {valid.water_km2.mean():.3f}.',
 f'Temperatură: mediană {valid.t2m_c.median():.2f} °C; IQR {valid.t2m_c.quantile(.25):.2f}–{valid.t2m_c.quantile(.75):.2f}.',
 f'Precipitație: mediană {valid.precip_mm.median():.2f} mm; IQR {valid.precip_mm.quantile(.25):.2f}–{valid.precip_mm.quantile(.75):.2f}.',
 f'Aria are distribuție asimetrică (skew={valid.water_km2.skew():.1f}); {100*(valid.water_km2==0).mean():.1f}% din rânduri au arie zero.',
 'valid_area_km2 este diagnostic JRC și nu intră în PCA.',
]
ax.text(.02,.34,'STATISTICI DESCRIPTIVE',transform=ax.transAxes,weight='bold',fontsize=8.5,color='#1b2a41',va='top')
ax.text(.02,.29,'\n'.join(stats),transform=ax.transAxes,fontsize=7.3,color='#39465a',va='top',linespacing=1.42,wrap=True)

ax=axs[1]; corr=valid[features].corr().to_numpy(); im=ax.imshow(corr,vmin=-1,vmax=1,cmap='RdBu_r')
names=['Arie','Temp.','Precip.','sin','cos']; ax.set_xticks(range(5),names,rotation=35,ha='right'); ax.set_yticks(range(5),names)
for i in range(5):
 for j in range(5): ax.text(j,i,f'{corr[i,j]:.2f}',ha='center',va='center',fontsize=7,color='white' if abs(corr[i,j])>.55 else '#202735')
ax.set_title('Corelații Pearson · r',loc='left',fontsize=10,color='#1b2a41',weight='bold')
fig.colorbar(im,ax=ax,fraction=.05,pad=.04)
ax.text(0,-.20,'JRC–temp.: 0,062\nJRC–precip.: −0,007',transform=ax.transAxes,fontsize=8,color='#39465a',va='top')

ax=axs[2]; x=np.arange(1,6)
ax.bar(x,evr*100,color='#5b8e7d',alpha=.85,label='Componentă')
ax.plot(x,np.cumsum(evr)*100,color='#c8702a',marker='o',label='Cumulat')
ax.set_xticks(x,[f'PC{i}' for i in x]); ax.set_ylabel('Varianță explicată (%)'); ax.set_ylim(0,105)
ax.grid(axis='y',color='#ded8cf'); ax.set_facecolor('#fffdf9')
ax.set_title('PCA standardizat · split temporal',loc='left',fontsize=10,color='#1b2a41',weight='bold')
ax.legend(frameon=False,fontsize=7,loc='center right')
ax.text(.02,-.20,f'Train: 2001–2017, n={len(train):,}\nTest: 2018–nov. 2021, n={len(test):,}\nPC1: {evr[0]*100:.1f}% · PC1–2: {evr[:2].sum()*100:.1f}%\nRMSE test, k=2: {np.sqrt(metrics[1]["test_standardized_reconstruction_mse"]):.3f} SD',
        transform=ax.transAxes,fontsize=7.5,color='#39465a',va='top',linespacing=1.35)
fig.text(.04,.025,'ERA5-Land: media pe poligon la scară ~11,132 m. Lipsurile nu sunt imputate; decembrie 2021 lipsește.',fontsize=8,color='#39465a')
fig.subplots_adjust(left=.055,right=.98,bottom=.24,top=.84,wspace=.42)
fig.savefig(OUT/'CP2_evidence_figure.png',dpi=200,facecolor=fig.get_facecolor())
summary={'export_rows':len(df),'lakes_exported':df.Hylak_id.nunique(),'months_exported':df.month.nunique(),'complete_X_rows':len(valid),'features':5,'lakes_with_complete_X':valid.Hylak_id.nunique(),'train_rows':len(train),'test_rows':len(test),'rows_missing_climate':int(df.t2m_c.isna().sum()),'december_2021_present':bool((df.month=='2021-12').any())}
pd.Series(summary).to_csv(OUT/'cp2_dataset_summary.csv',header=['value'])
print(summary); print('EVR',evr); print(loads.round(3)); print(pd.DataFrame(metrics).to_string(index=False))
