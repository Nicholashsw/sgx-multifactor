import warnings; warnings.filterwarnings("ignore")
import pandas as pd, numpy as np, statsmodels.api as sm
q=pd.read_csv('sg_broad_quarterly.csv',parse_dates=['Date']).sort_values(['SecID','Date'])
q=q[q['Date']>='1991-01-01'].copy(); q['Ret']=q['Return_1M']
dts=sorted(q['Date'].unique()); TOPN=100
def uni(d):
    c=q[q['Date']==d].dropna(subset=['MKT_CAP']); return c.nlargest(TOPN,'MKT_CAP')
bench={};bwt={}
for i,d in enumerate(dts[:-1]):
    u=uni(d)
    if len(u)<30: continue
    nd=dts[i+1]; nr=q[q['Date']==nd].drop_duplicates('SecID').set_index('SecID')['Ret']
    w=u.set_index('SecID')['MKT_CAP']; w/=w.sum(); r=nr.reindex(w.index); m=r.notna()
    if m.sum()>10:
        bench[nd]=float((r[m]*w[m]).sum()/w[m].sum())
        bwt[nd]=(u.assign(w=(u['MKT_CAP']/u['MKT_CAP'].sum()).values), nr)
bench=pd.Series(bench).sort_index()
def nwa(r,lab):
    r=r.dropna(); df=pd.concat([r,bench],axis=1,keys=['s','b']).dropna()
    m=sm.OLS(df['s'],sm.add_constant(df['b'])).fit(cov_type='HAC',cov_kwds={'maxlags':6})
    c=(1+r).cumprod()
    return {'Design':lab,'Ann%':round(((1+r).prod()**(12/len(r))-1)*100,1),
            'Sharpe':round(r.mean()/r.std()*np.sqrt(12),2),'MaxDD%':round(((c-c.cummax())/c.cummax()).min()*100,1),
            'Alpha%mo':round(m.params['const']*100,3),'t':round(m.tvalues['const'],2),'Beta':round(m.params['b'],2),'N':len(r)}

# ---- A. SECTOR-NEUTRAL RANKING ----
q['Comp_SN']=q['Composite']-q.groupby(['Date','gsector'])['Composite'].transform('mean')
def run(score,cost_ls=0.002,cost_l=0.001):
    L={};S={};TO=[]
    prev=set()
    for i,d in enumerate(dts[:-1]):
        u=uni(d).dropna(subset=[score])
        if len(u)<40: continue
        k=max(5,len(u)//5); u=u.sort_values(score,ascending=False)
        lg,sh=u.head(k),u.tail(k)
        nd=dts[i+1]; nr=q[q['Date']==nd].drop_duplicates('SecID').set_index('SecID')['Ret']
        rl=nr.reindex(lg['SecID']); rs=nr.reindex(sh['SecID'])
        if rl.notna().sum()<3 or rs.notna().sum()<3: continue
        cur=set(lg['SecID']); TO.append(len(cur-prev)/max(len(cur),1)); prev=cur
        L[nd]=rl.mean(); S[nd]=rs.mean()
    L=pd.Series(L).sort_index(); S=pd.Series(S).sort_index()
    return (L-cost_l), (L-S-cost_ls), float(np.mean(TO))
lo_b,ls_b,to_b=run('Composite'); lo_s,ls_s,to_s=run('Comp_SN')
print("=== A. SECTOR-NEUTRAL vs plain ranking (PIT top-100, EW quintile) ===")
print(pd.DataFrame([nwa(ls_b,'Plain composite [L/S]'),nwa(ls_s,'Sector-neutral [L/S]'),
                    nwa(lo_b,'Plain composite [Long]'),nwa(lo_s,'Sector-neutral [Long]')]).to_string(index=False))
print(f"  monthly long turnover: plain {to_b:.1%} | sector-neutral {to_s:.1%}")

# ---- B. BRINSON-FACHLER (long book vs cap-weighted universe) ----
GICS={10:'Energy',15:'Materials',20:'Industrials',25:'ConsDisc',30:'ConsStap',35:'HealthCare',
      40:'Financials',45:'InfoTech',50:'CommSvcs',55:'Utilities',60:'RealEstate'}
alloc=[];sel=[];inter=[];tot=[]
for i,d in enumerate(dts[:-1]):
    u=uni(d).dropna(subset=['Composite'])
    if len(u)<40 or dts[i+1] not in bwt: continue
    k=max(5,len(u)//5); lg=u.sort_values('Composite',ascending=False).head(k)
    bu,nr=bwt[dts[i+1]]
    bu=bu.assign(r=nr.reindex(bu['SecID']).values).dropna(subset=['r'])
    lgv=lg.assign(r=nr.reindex(lg['SecID']).values).dropna(subset=['r'])
    if len(lgv)<3 or len(bu)<20: continue
    bu['w']=bu['w']/bu['w'].sum()
    rB=float((bu['r']*bu['w']).sum())
    A=S=I=0.0
    for sec in set(bu['gsector']).union(lgv['gsector']):
        bs=bu[bu['gsector']==sec]; ps=lgv[lgv['gsector']==sec]
        wB=float(bs['w'].sum()); wP=len(ps)/len(lgv)
        rBs=float((bs['r']*bs['w']).sum()/bs['w'].sum()) if wB>0 else 0.0
        rPs=float(ps['r'].mean()) if len(ps) else 0.0
        A+= (wP-wB)*(rBs-rB)
        S+= wB*(rPs-rBs) if wB>0 else 0.0
        I+= (wP-wB)*(rPs-rBs) if wB>0 else 0.0
    alloc.append(A);sel.append(S);inter.append(I);tot.append(float(lgv['r'].mean())-rB)
print("\n=== B. BRINSON-FACHLER, long book vs cap-weighted universe ===")
print(f"  Allocation  : {np.mean(alloc)*1200:+.2f} %/yr")
print(f"  Selection   : {np.mean(sel)*1200:+.2f} %/yr")
print(f"  Interaction : {np.mean(inter)*1200:+.2f} %/yr")
print(f"  Sum         : {(np.mean(alloc)+np.mean(sel)+np.mean(inter))*1200:+.2f} %/yr")
print(f"  Actual active return (check): {np.mean(tot)*1200:+.2f} %/yr")

# ---- C. OVERLAYS re-run ON PIT universe ----
print("\n=== C. Overlays on PIT universe (closes the 'unfiltered' caveat) ===")
rows=[nwa(ls_b,'1. Baseline L/S')]
def voltarget(r,target=0.12,win=12,cap=2.0):
    rv=r.rolling(win,min_periods=6).std()*np.sqrt(12)
    return r*(target/rv).shift(1).clip(0,cap).fillna(1.0)
rows.append(nwa(voltarget(ls_b).dropna(),'2. + vol target 12%'))
rows.append(nwa(voltarget(ls_s).dropna(),'3. sector-neutral + vol target'))
print(pd.DataFrame(rows).to_string(index=False))

# ---- D. COST SENSITIVITY / BREAK-EVEN ----
print("\n=== D. Cost sensitivity, long-short (turnover %.0f%%/mo both legs) ==="%(to_b*100))
g=(ls_b+0.002)  # gross
for c in [0,10,20,40,60,80]:
    r=(g-2*to_b*c/1e4).dropna()
    s=nwa(r,f'{c}bp'); print(f"  {c:3d}bp one-way: Sharpe {s['Sharpe']:+.2f}  alpha {s['Alpha%mo']:+.3f}%/mo  t {s['t']:+.2f}")
gm=g.mean()
print(f"  break-even one-way cost = gross mean / (2*turnover) = {gm/(2*to_b)*1e4:.0f} bp")
