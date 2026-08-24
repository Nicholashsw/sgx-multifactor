import pandas as pd, numpy as np
def num(s): return pd.to_numeric(s,errors='coerce')

# --- monthly PIT price panel (366 tickers)
p=pd.read_csv('x/S3_PriceData_PIT.csv',low_memory=False)
p['Date']=pd.to_datetime(p.Date,errors='coerce')+pd.offsets.MonthEnd(0)
for c in ['PX_LAST','TOT_RET_IDX','MKT_CAP','PX_TO_BOOK','DIV_YIELD','PX_VOLUME']: p[c]=num(p[c])
p=p.dropna(subset=['Date','Ticker']).sort_values(['Ticker','Date'])
print('monthly PIT panel:',p.shape,'tickers',p.Ticker.nunique(),p.Date.min().date(),p.Date.max().date())

# --- daily high/low -> true 52w high
hl=pd.concat([pd.read_csv(f'x/S3_DailyHL_PIT_{i}.csv',low_memory=False,usecols=['Date','Ticker','PX_HIGH','PX_LOW']) for i in (1,2)])
hl['Date']=pd.to_datetime(hl.Date,errors='coerce'); hl['PX_HIGH']=num(hl.PX_HIGH)
hl=hl.dropna(subset=['Date','Ticker','PX_HIGH'])
hl['ym']=hl.Date.values.astype('datetime64[M]')
mh=hl.groupby(['Ticker','ym']).PX_HIGH.max().reset_index()
mh['Date']=mh.ym+pd.offsets.MonthEnd(0)
print('daily HL -> monthly max:',mh.shape,'tickers',mh.Ticker.nunique())
p=p.merge(mh[['Ticker','Date','PX_HIGH']],on=['Ticker','Date'],how='left')

g=p.groupby('Ticker')
p['Ret_1M']=g['TOT_RET_IDX'].pct_change()
p['MOM_12_1']=g['TOT_RET_IDX'].shift(1)/g['TOT_RET_IDX'].shift(12)-1
p['REV_1M']=-p['Ret_1M']
p['High12_daily']=g['PX_HIGH'].transform(lambda s:s.rolling(12,min_periods=12).max())
p['High12_close']=g['PX_LAST'].transform(lambda s:s.rolling(12,min_periods=12).max())
p['PH']=p.PX_LAST/p.High12_daily
p['PH_close']=p.PX_LAST/p.High12_close
p['ADV']=g.apply(lambda d:(d.PX_VOLUME*d.PX_LAST).rolling(6,min_periods=3).mean(),include_groups=False).reset_index(level=0,drop=True)
p['Fwd_1M']=g['Ret_1M'].shift(-1)
p=p[(p.PX_LAST>0.02)&p.Ret_1M.between(-0.9,3.0)]

# --- PIT STI membership (quarterly snapshots -> monthly forward-fill)
pm=pd.read_csv('pit_members_long.csv')
pm=pm[pm.Index=='STI'].copy()
pm['Snap']=pd.to_datetime(pm.Snap.astype(str),format='%Y%m%d')+pd.offsets.MonthEnd(0)
pm['Ticker']=pm.Tkr.str.strip()+' Equity'
snaps=sorted(pm.Snap.unique())
rows=[]
allm=sorted(p.Date.unique())
for i,s in enumerate(snaps):
    end=snaps[i+1] if i+1<len(snaps) else max(allm)
    mem=pm[pm.Snap==s].Ticker.tolist()
    for d in [d for d in allm if s<=d<end]:
        rows+= [{'Date':d,'Ticker':t,'inSTI':1} for t in mem]
sti_mem=pd.DataFrame(rows).drop_duplicates()
print('PIT STI membership months:',sti_mem.Date.nunique(),'| avg names',sti_mem.groupby("Date").Ticker.nunique().mean().round(1))

# --- BEQS PIT broad membership (top ~208 by mktcap, 36 snapshots)
b=pd.read_csv('x/S3_BEQS_Members.csv',low_memory=False)
b['Snap']=pd.to_datetime(b.SnapshotDate.astype(str),format='%Y%m%d')+pd.offsets.MonthEnd(0)
bs=sorted(b.Snap.unique()); rows=[]
for i,s in enumerate(bs):
    end=bs[i+1] if i+1<len(bs) else max(allm)
    mem=b[b.Snap==s].Ticker.tolist()
    for d in [d for d in allm if s<=d<end]:
        rows+=[{'Date':d,'Ticker':t,'inBEQS':1} for t in mem]
beqs=pd.DataFrame(rows).drop_duplicates()
print('BEQS PIT months:',beqs.Date.nunique(),'| avg names',beqs.groupby("Date").Ticker.nunique().mean().round(1))

p=p.merge(sti_mem,on=['Date','Ticker'],how='left').merge(beqs,on=['Date','Ticker'],how='left')
p[['inSTI','inBEQS']]=p[['inSTI','inBEQS']].fillna(0)
p.to_csv('pit_panel.csv',index=False)
print('\nfinal panel',p.shape)
print('coverage of PH (daily-high based):',p.PH.notna().sum(),'| close-based:',p.PH_close.notna().sum())
print('PIT-STI rows:',int(p.inSTI.sum()),'| BEQS rows:',int(p.inBEQS.sum()))
