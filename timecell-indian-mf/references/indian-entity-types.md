# Indian Entity Types — MF Holding Context

> Reference for entity-specific MF tax treatment, KYC requirements, and typical holding patterns. Used by mf-review command when analyzing multi-entity MF portfolios.

## HUF (Hindu Undivided Family)

**Structure:** Separate tax entity with own PAN. Karta manages, coparceners have rights.
**MF holding pattern:** Commonly holds equity MFs and ELSS for additional 80C deduction (separate from individual limit).
**Tax treatment:**
- LTCG (equity, >1Y): 12.5% above Rs 1.25L (same as individual)
- STCG (equity, <1Y): 20%
- Debt fund gains: taxed at slab rate (post-2023 amendment, no indexation)
**SEBI KYC category:** HUF (separate from individual KYC)
**Key consideration:** HUF partition affects all MF holdings — flag if partition_status is not "undivided"

## Private Limited Company

**Structure:** ROC-registered company with CIN. Board resolution needed for MF investments.
**MF holding pattern:** Typically parks surplus in liquid/overnight/ultra-short debt funds. Some hold equity MFs for treasury management.
**Tax treatment:**
- All MF gains taxed at corporate rate (25.17% for turnover < Rs 400Cr)
- No distinction between LTCG/STCG for company — all at corporate rate
- Dividend income taxed at corporate rate
**SEBI KYC category:** Non-Individual (corporate)
**Key consideration:** Board resolution required for each MF investment. Authorized signatory list matters.

## LLP (Limited Liability Partnership)

**Structure:** MCA-registered partnership with LLPIN. Designated partners manage.
**MF holding pattern:** Similar to company — surplus parking in debt funds. Less common for equity.
**Tax treatment:**
- MF gains taxed at firm rate (30% + 12% surcharge if income > Rs 1Cr)
- No LTCG/STCG distinction at firm level
- No DDT (post-2020), dividend taxed at firm rate
**SEBI KYC category:** Non-Individual (partnership/LLP)
**Key consideration:** LLP agreement must authorize MF investments.

## Trust (Private)

**Structure:** Trustee-held assets for beneficiaries. Discretionary or specific.
**MF holding pattern:** Varies by trust deed. Common for intergenerational wealth transfer.
**Tax treatment:**
- Specific trust: taxed in hands of beneficiaries at their slab rates
- Discretionary trust: taxed at maximum marginal rate (MMR, ~42.7%)
- Irrevocable specific trust with identifiable beneficiaries: pass-through
**SEBI KYC category:** Non-Individual (trust)
**Key consideration:** Trust deed restrictions may limit MF categories (e.g., "only debt funds" clause). Check deed before recommending equity MFs.

## Partnership Firm

**Structure:** Registered or unregistered partnership under Indian Partnership Act.
**MF holding pattern:** Surplus parking in debt funds. Equity MFs less common.
**Tax treatment:**
- All income taxed at firm rate (30% + surcharge)
- Interest on capital to partners: deductible up to 12%
- No LTCG/STCG distinction at firm level
**SEBI KYC category:** Non-Individual (partnership)
**Key consideration:** Partnership deed must authorize MF investments. All partners' KYC required.

## AIF (Alternative Investment Fund)

**Structure:** SEBI-registered pooled investment vehicle. Categories I, II, III.
**MF holding relevance:** AIFs are NOT direct MF holders, but principals who invest in AIFs may also hold direct MFs. Include AIF exposure in total portfolio allocation analysis.
**Tax treatment:**
- Category I/II: pass-through (taxed at investor level)
- Category III: fund-level taxation at MMR
**SEBI KYC category:** SEBI-registered entity (separate regime)
**Key consideration:** When computing total MF exposure, include any MF-holding AIFs the principal has invested in.

## Cross-Entity Summary

| Entity Type | MF LTCG (Equity) | MF STCG (Equity) | Debt MF Gains | KYC Type |
|------------|------------------|------------------|---------------|----------|
| Individual | 12.5% > Rs 1.25L | 20% | Slab rate | Individual |
| HUF | 12.5% > Rs 1.25L | 20% | Slab rate | HUF |
| Private Ltd | Corporate rate | Corporate rate | Corporate rate | Non-Individual |
| LLP | 30% + surcharge | 30% + surcharge | 30% + surcharge | Non-Individual |
| Trust (Specific) | Beneficiary slab | Beneficiary slab | Beneficiary slab | Non-Individual |
| Trust (Discretionary) | MMR (~42.7%) | MMR (~42.7%) | MMR (~42.7%) | Non-Individual |
| Partnership | 30% + surcharge | 30% + surcharge | 30% + surcharge | Non-Individual |
