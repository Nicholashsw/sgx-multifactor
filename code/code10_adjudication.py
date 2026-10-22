# Run on 2026-10-22. Adjudicates the 115 code-10 exits into the four-category
# delisting taxonomy (cash takeout / stock merger / solvent liquidation /
# suspension-insolvency) using only evidence already on file: the SDC match
# (code10_with_sdc.csv), the hand-adjudicated Factiva/BT verdicts
# (verdict_ledger.csv) and the residual Factiva worksheet. Anything those files
# do not settle is UNRESOLVED; price-based triage is not treated as evidence.
# Then re-runs the terminal-return sensitivity of survivorship_sensitivity.py.
# Run from the local data folder; writes the firm-level worksheet there (vendor
# rows, never committed) and only aggregates to results/verified/.
import sys, pandas as pd
out_dir=sys.argv[1] if len(sys.argv)>1 else '.'
p=pd.read_csv('sgp_panel_monthly.csv',parse_dates=['Date'],low_memory=False)
p=p[(p.Date>="1995-01-31") & p.Ret_1M.notna()].copy()
p=p.merge(p.groupby("gvkey")["dlrsn"].last().rename("exit_reason"),on="gvkey",how="left")
ann=lambda s:((1+s).prod()**(12/len(s))-1)*100
def bias(frame):
    pit=frame.groupby("Date")["Ret_1M"].mean()
    look=frame[frame.exit_reason.isna()].groupby("Date")["Ret_1M"].mean().reindex(pit.index).dropna()
    return ann(look)-ann(pit.reindex(look.index))
def force_wipe(frame,gvkeys):
    f=frame.copy(); last=f.loc[f.groupby("gvkey").tail(1).index]
    f.loc[last[last.gvkey.isin(gvkeys)].index,"Ret_1M"]=-1.0
    return f

ws=pd.read_csv('code10_with_sdc.csv')
led=pd.read_csv('verdict_ledger.csv').set_index('gvkey')
LEDGER={'TAKEOUT_COMPLETED':'cash takeout','MERGER_COMPLETED':'stock merger',
        'SOLVENT_LIQUIDATION':'solvent liquidation','WIPEOUT_CONFIRMED':'suspension-insolvency'}
def adjudicate(r):
    if r.gvkey in led.index:
        v=led.loc[r.gvkey]
        return LEDGER[v.verdict_CONFIRMED],'Factiva/BT hand adjudication',''
    if r.match_src=='SDC completed':
        flag='SDC effective date >3m from last panel month' if abs(r.gap_months)>3 else ''
        return 'takeout, consideration not in SDC extract','SDC completed deal',flag
    if r.match_src=='SDC withdrawn':
        return 'UNRESOLVED','SDC withdrawn bid only; no completed deal',''
    return 'UNRESOLVED','no SDC deal; Factiva query not yet run',''
ws[['category','evidence','flag']]=ws.apply(lambda r:pd.Series(adjudicate(r)),axis=1)
ws.to_csv(f'{out_dir}/code10_adjudicated_2026-10-22.csv',index=False)

wipe_conf=set(ws.loc[ws.category=='suspension-insolvency','gvkey'])
unres=set(ws.loc[ws.category=='UNRESOLVED','gvkey'])
unres_wipe=set(ws.loc[(ws.category=='UNRESOLVED')&(ws.triage_prior=='likely_wipeout'),'gvkey'])
unres_wa=set(ws.loc[(ws.category=='UNRESOLVED')&ws.triage_prior.isin(['likely_wipeout','ambiguous']),'gvkey'])
old_w=set(ws.loc[ws.triage_prior=='likely_wipeout','gvkey']); old_a=set(ws.loc[ws.triage_prior=='ambiguous','gvkey'])
rows=[('before','baseline, no terminal adjustment',0,bias(p)),
      ('before','37 triaged wipeouts forced -100%',len(old_w),bias(force_wipe(p,old_w))),
      ('before','37 + 25 ambiguous forced -100%',len(old_w|old_a),bias(force_wipe(p,old_w|old_a))),
      ('after','confirmed insolvencies forced -100%',len(wipe_conf),bias(force_wipe(p,wipe_conf))),
      ('after','+ unresolved triaged wipeouts',len(wipe_conf|unres_wipe),bias(force_wipe(p,wipe_conf|unres_wipe))),
      ('after','+ unresolved triaged wipeouts and ambiguous',len(wipe_conf|unres_wa),bias(force_wipe(p,wipe_conf|unres_wa))),
      ('after','+ every unresolved exit (harshest)',len(wipe_conf|unres),bias(force_wipe(p,wipe_conf|unres)))]
res=pd.DataFrame(rows,columns=['stage','scenario','n_forced','bias_pp_yr']).round({'bias_pp_yr':2})
cats=ws.groupby(['category','evidence']).size().rename('n').reset_index()
cross=pd.crosstab(ws.category,ws.triage_prior)
print(cats.to_string(index=False)); print(); print(cross); print(); print(res.to_string(index=False))
print('flagged:',int((ws.flag!='').sum()))
res.to_csv('code10_sensitivity_2026-10-22.csv',index=False)
cats.to_csv('code10_category_counts_2026-10-22.csv',index=False)
cross.to_csv('code10_category_by_triage_2026-10-22.csv')
