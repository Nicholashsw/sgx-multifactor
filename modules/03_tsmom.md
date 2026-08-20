# Module 3. Time-series momentum

Standalone: Moskowitz-Ooi-Pedersen TSMOM on the survivorship-clean liquid100 universe at k=3 earns Sharpe 0.974 (t=4.65, 2001-2026); the 30-name Bloomberg 0.876 is survivorship-inflated (PIT counterpart 0.565), and pre-2001 is a null. Horizon peaks at h=3-5 (t=2.55) and fades by h=12; h=3 is a searched cell, priced by block bootstrap. A one-month implementation lag halves the wide-universe Sharpe (0.727 to 0.510).

The module finding is the combination reversal: pre-borrow the fundamental sleeve plus TSMOM diversified (correlation -0.14); borrow-constrained and fully costed on the matched 2003+ window the correlation rises to +0.333 and the combination Sharpe (0.460) falls below TSMOM alone (0.543). Attribution: the fundamental sleeve dies in its own leakage waterfall (0.810 to -0.013%/mo, top ten names 83% of P&L) while TSMOM survives (0.773 to 0.576) on breadth.

Evidence: REPORT_FINAL.md section 9.1; ledger rows H1-H8. Figures: tsmom_*.
