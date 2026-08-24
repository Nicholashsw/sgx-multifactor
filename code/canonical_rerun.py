"""
CANONICAL RE-RUN — broad-universe paper. Single source of truth.
Requires: sg_broad_quarterly.csv (P-Q panel), World_Index_Constituents.csv, Monthly_World_Indices.csv
Produces every number in Tables 1-3 from ONE panel (P-Q, quarterly/TTM, 4-month lag).
Run:  python3 canonical_rerun.py
"""
import warnings; warnings.filterwarnings("ignore")
import pandas as pd, numpy as np, statsmodels.api as sm
from scipy import stats
import os, json

PANEL='sg_broad_quarterly.csv'; CONST='World_Index_Constituents.csv'; BENCH='more/Monthly_World_Indices.csv'
for f in [PANEL,CONST,BENCH]:
    if not os.path.exists(f): raise SystemExit(f"MISSING: {f}")

q=pd.read_csv(PANEL,parse_dates=['Date']).sort_values(['SecID','Date'])
q=q[q['Date']>='1991-01-01']
wc=pd.read_csv(CONST,parse_dates=['JuneDate']); wc['SecID']=wc['gvkey'].astype(str)+'_'+wc['iid'].astype(str)
snaps=sorted(wc['JuneDate'].unique())
def members(d):
    v=[s for s in snaps if s<=d]
    return set(wc[wc['JuneDate']==v[-1]]['SecID']) if v else None
mw=pd.read_csv(BENCH); mw['date']=pd.to_datetime(mw['date'])+pd.offsets.MonthEnd(0)
bench=mw[mw['fic']=='SGP'].set_index('date')['mportret']
dts=sorted(q['Date'].unique())
def tier_of(g):
    g=g.sort_values('MKT_CAP',ascending=False).reset_index(); g['r']=np.arange(len(g))
    g['Tier']=np.where(g['r']<30,'Large',np.where(g['r']<100,'Mid','Small')); return g.set_index('index')['Tier']
def alpha(r):
    df=pd.concat([r,bench],axis=1,keys=['s','b']).dropna()
    m=sm.OLS(df['s'],sm.add_constant(df['b'])).fit(cov_type='HAC',cov_kwds={'maxlags':6})
    return m.params['const']*100, m.tvalues['const'], m.params['b']
def perf(r):
    r=r.dropna(); c=(1+r).cumprod()
    return dict(ann=((1+r).prod()**(12/len(r))-1)*100, sharpe=r.mean()/r.std()*np.sqrt(12),
                mdd=((c-c.cummax())/c.cummax()).min()*100, n=len(r))
OUT={}

# ---- 0. UNIVERSE COUNTS (fixes the "352" error) ----
pit_n=[]
for d in dts:
    am=members(d)
    if am is None: continue
    pit_n.append(q[(q['Date']==d)&(q['SecID'].isin(am))]['SecID'].nunique())
OUT['universe']={'unfiltered_avg_per_month':float(q.groupby('Date')['SecID'].count().mean()),
                 'PIT_avg_per_month':float(np.mean(pit_n)),'PIT_min':int(np.min(pit_n)),'PIT_max':int(np.max(pit_n)),
                 'months':len(dts),'companies':int(q['SecID'].nunique())}
print("UNIVERSE:",OUT['universe'])

# ---- 1. TABLE 1: factor ICs on PIT universe, P-Q panel ----
q['Fwd']=q.groupby('SecID')['Return_1M'].shift(-1)
zc=[c for c in q.columns if c.startswith('Z_')]+['Composite']
t1=[]
for c in zc:
    ics=[]
    for d,g in q.groupby('Date'):
        am=members(d)
        if am is None: continue
        sub=g[g['SecID'].isin(am)][[c,'Fwd']].dropna()
        if len(sub)>=15: ics.append(stats.spearmanr(sub[c],sub['Fwd'])[0])
    if len(ics)>50:
        a=np.array(ics); t1.append({'Factor':c,'Mean_IC':round(a.mean(),4),
            't':round(a.mean()/(a.std()/np.sqrt(len(a))),2),'n':len(a)})
T1=pd.DataFrame(t1).sort_values('t',ascending=False); OUT['table1']=T1.to_dict('records')
print("\nTABLE 1 (PIT, P-Q):\n",T1.to_string(index=False))

# ---- 2. TABLE 2: survivor vs PIT, returns AND alphas from same panel ----
def bt(pit,tier=None,liq=False):
    surv=set(q[q['Date']==dts[-1]]['SecID']); rows=[]
    for i,d in enumerate(dts[:-1]):
        c=q[q['Date']==d].dropna(subset=['Composite']).copy()
        if pit:
            am=members(d)
            if am is None: continue
            c=c[c['SecID'].isin(am)]
        else: c=c[c['SecID'].isin(surv)]
        if tier:
            if len(c)<40: continue
            c['Tier']=tier_of(c); c=c[c['Tier']==tier]
            if liq and c['Amihud'].notna().sum()>4: c=c[c['Amihud']<=c['Amihud'].quantile(.8)]
            k=max(3,len(c)//5)
        else:
            k=max(5,len(c)//10)
        if len(c)<(8 if tier else 20): continue
        c=c.sort_values('Composite',ascending=False)
        nd=dts[i+1]; nr=q[q['Date']==nd].drop_duplicates('SecID').set_index('SecID')['Return_1M']
        L=nr.reindex(c.head(k)['SecID']).mean(); S=nr.reindex(c.tail(k)['SecID']).mean()
        rows.append({'Date':nd,'Long':L-0.001,'LS':L-S-0.002,'n':len(c)})
    return pd.DataFrame(rows).set_index('Date')
t2=[]
for lbl,pit in [('Survivor-only',False),('Point-in-time',True)]:
    b=bt(pit)
    for leg in ['Long','LS']:
        p=perf(b[leg]); a,t,be=alpha(b[leg].dropna())
        t2.append({'Universe':lbl,'Leg':leg,'Ann%':round(p['ann'],1),'Sharpe':round(p['sharpe'],2),
                   'MaxDD%':round(p['mdd'],1),'Alpha%mo':round(a,2),'Alpha_t':round(t,2),'Beta':round(be,2)})
T2=pd.DataFrame(t2); OUT['table2']=T2.to_dict('records')
print("\nTABLE 2 (P-Q, returns+alphas same panel):\n",T2.to_string(index=False))

# ---- 3. TABLE 3: size tiers + liquidity screen ----
t3=[]
for tier in ['Large','Mid','Small']:
    b=bt(True,tier=tier); p=perf(b['LS']); a,t,be=alpha(b['LS'].dropna())
    ics=[]
    for d,g in q.groupby('Date'):
        am=members(d)
        if am is None: continue
        c=g[g['SecID'].isin(am)].dropna(subset=['Composite','Fwd']).copy()
        if len(c)<40: continue
        c['Tier']=tier_of(c); c=c[c['Tier']==tier]
        if len(c)>=8: ics.append(stats.spearmanr(c['Composite'],c['Fwd'])[0])
    ia=np.array(ics)
    t3.append({'Tier':tier,'AvgNames':int(b['n'].mean()),'IC':round(ia.mean(),4),
               'IC_t':round(ia.mean()/(ia.std()/np.sqrt(len(ia))),2),'LS_Ann%':round(p['ann'],1),
               'LS_Sharpe':round(p['sharpe'],2),'Alpha%mo':round(a,2),'Alpha_t':round(t,2),'Beta':round(be,2)})
b=bt(True,tier='Small',liq=True); p=perf(b['LS']); a,t,be=alpha(b['LS'].dropna())
t3.append({'Tier':'Small (liq-screen)','AvgNames':int(b['n'].mean()),'IC':None,'IC_t':None,
           'LS_Ann%':round(p['ann'],1),'LS_Sharpe':round(p['sharpe'],2),'Alpha%mo':round(a,2),
           'Alpha_t':round(t,2),'Beta':round(be,2)})
T3=pd.DataFrame(t3); OUT['table3']=T3.to_dict('records')
print("\nTABLE 3 (PIT tiers, P-Q):\n",T3.to_string(index=False))

json.dump(OUT,open('canonical_results.json','w'),indent=1,default=str)
T1.to_csv('canonical_table1.csv',index=False); T2.to_csv('canonical_table2.csv',index=False); T3.to_csv('canonical_table3.csv',index=False)
print("\nSaved canonical_results.json + canonical_table{1,2,3}.csv")
