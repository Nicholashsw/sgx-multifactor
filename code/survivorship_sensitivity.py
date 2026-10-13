# Executed 2026-08-20 (consolidation pass). Terminal-return sensitivity of the SGX
# delisting-survivorship bias, on the real Compustat Global SGP monthly panel.
# Replicates SGX_Survivorship_Decomposition.ipynb CELL 5 exactly, then forces
# -100% final-month returns on adjudication subsets from the code-10 worksheets.
import pandas as pd
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
ws=pd.read_csv('code10_classification_worksheet.csv')
short=pd.read_csv('code10_residual_shortlist.csv')
wipe=set(ws.loc[ws.triage_prior=='likely_wipeout','gvkey'])
amb=set(ws.loc[ws.triage_prior=='ambiguous','gvkey'])
print("baseline", round(bias(p),2))                       # -0.89
print("37 wipeouts forced -100%", round(bias(force_wipe(p,wipe)),2))        # -0.60
print("37+25 ambiguous forced", round(bias(force_wipe(p,wipe|amb)),2))      # -0.40
print("53 residual no-deal forced", round(bias(force_wipe(p,set(short['gvkey']))),2))  # -0.44
