# Run on 2026-10-22. Post-freeze robustness test closing limitation L6: naive
# inverse-realised-volatility scaling as a benchmark for the regime/sizing
# overlays, on the same window, rebalance and costs as the overlay test.
# Input: garch_weights.csv from the SGX3 overlay run (STI-core monthly net
# returns after costs, benchmark, and each overlay's weights). Run from the
# folder holding it. The script first reproduces the published GARCH-sizing
# table exactly (ledger L3, E21), which pins the conventions it then reuses:
#   excess return = w_t * (net_t - rf), rf = 1.412%/yr constant
#   weights rescaled to the jump overlay's mean exposure, 1.3639x
#   jump-aware weights capped at 1.5 before rescaling
# Benchmark (fixed before running): w_t = 1 / sd of the strategy's own net
# monthly returns over the 12 months to t-1 (min 6, else w=1), rescaled the
# same way. No cap. A 6-month window is reported as a sensitivity only.
import sys, json, numpy as np, pandas as pd
out=sys.argv[1] if len(sys.argv)>1 else '.'
d=pd.read_csv('garch_weights.csv',parse_dates=['Date'])
r=d.net; RF=0.0011766666666666644; L=1.3639147449043758
sh=lambda x:x.mean()/x.std()*np.sqrt(12)
def lev(w): w=pd.Series(w,index=d.index); return w*L/w.mean()
def ivol_w(n):
    w=1/r.rolling(n,min_periods=6).std().shift(1)
    w=w/w.dropna().mean(); return w.fillna(1.0)
legs={'Baseline (1.00x)':pd.Series(1.0,index=d.index),
      'Constant 1.36x leverage':lev(np.ones(len(d))),
      'Jump-aware ES-target @ 1.36x':lev(d.w_jump.clip(upper=1.5)),
      'GARCH vol-target (LAGGED) @ 1.36x':lev(d.w_garch_lag),
      'Inverse realised vol 12m @ 1.36x':lev(ivol_w(12)),
      'Inverse realised vol 6m @ 1.36x (sensitivity)':lev(ivol_w(6))}
ex={k:w*(r-RF) for k,w in legs.items()}
def mdd(x): c=(1+x).cumprod(); return ((c/c.cummax())-1).min()*100
tab=pd.DataFrame([{'label':k,'AvgExp':legs[k].mean(),'Sharpe':sh(x),'Ann%':x.mean()*1200,
                   'Vol%':x.std()*np.sqrt(12)*100,'MaxDD%':mdd(legs[k]*r)} for k,x in ex.items()])
pub={'Baseline (1.00x)':0.7755663879562852,'Constant 1.36x leverage':0.7755663879562852,
     'Jump-aware ES-target @ 1.36x':0.837683901791648,'GARCH vol-target (LAGGED) @ 1.36x':0.7340136310844769}
for k,v in pub.items(): assert abs(sh(ex[k])-v)<1e-9, f'does not reproduce {k}'
# paired circular block bootstrap of Sharpe differences vs the 12m benchmark
rng=np.random.default_rng(20261022); n=len(d); B=10000; blk=6
starts=rng.integers(0,n,(B,-(-n//blk))); idx=((starts[:,:,None]+np.arange(blk))%n).reshape(B,-1)[:,:n]
bench=ex['Inverse realised vol 12m @ 1.36x'].to_numpy()
def bsh(a): return a.mean(1)/a.std(1,ddof=1)*np.sqrt(12)
rows=[]
for k in ['Constant 1.36x leverage','Jump-aware ES-target @ 1.36x','GARCH vol-target (LAGGED) @ 1.36x']:
    a=ex[k].to_numpy(); diff=bsh(a[idx])-bsh(bench[idx]); obs=sh(ex[k])-sh(ex['Inverse realised vol 12m @ 1.36x'])
    rows.append({'overlay':k,'sharpe_minus_ivol':obs,'ci_lo':np.percentile(diff,2.5),'ci_hi':np.percentile(diff,97.5),
                 'p_gt0':(diff>0).mean(),'beats_bar_+0.10':bool(obs>=0.10 and np.percentile(diff,2.5)>0)})
cmp=pd.DataFrame(rows)
pd.set_option('display.width',200)
print(f'window {d.Date.min():%Y-%m} to {d.Date.max():%Y-%m}, {n} monthly obs (published GARCH-test frame reproduced exactly)')
print(tab.round(3).to_string(index=False)); print(); print(cmp.round(3).to_string(index=False))
tab.round(4).to_csv(f'{out}/ivol_benchmark_table.csv',index=False)
cmp.round(4).to_csv(f'{out}/ivol_benchmark_vs_overlays.csv',index=False)
