"""Harmonized political science graduate enrollment, 1975-2025.

Before 2017 GSS code 907 lumps political science with international relations, public policy and
public administration. For each institution and fall, split its 907 count across those four fields in
proportion to the institution's IPEDS master's and doctoral completions in each field, weighting
completions by a stock multiplier (enrolled students per annual graduate) and averaging over a window
of completion years after the fall in question.

Validation: from 2017, GSS reports 907 (political science), 912 (IR) and 914 (public policy) separately
and public administration is out of scope. Applying the same rule to 907+912+914 for 2017-2025 and
comparing the predicted political science count with the actual 907 count tests the method.

Usage: python harmonize_polisci.py data/gss_units data/ipeds_completions_polisci_fields.csv
"""
import sys
import numpy as np
import pandas as pd

import glob, os
src = sys.argv[1]
files = sorted(glob.glob(os.path.join(src, "*.csv"))) if os.path.isdir(src) else [src]
g = pd.concat(pd.read_csv(f, dtype={"gss_code": str, "year": str}, low_memory=False) for f in files)
c = pd.read_csv(sys.argv[2])
g = g[g.year.str.fullmatch(r"\d{4}")].copy()
g["year"] = g.year.astype(int)
g["n"] = g.pt_tot_all_races_v.fillna(0) + g.ft_tot_all_races_v.fillna(0)
g = g[g.gss_code.isin(["907", "912", "914"])]
g["inst"] = g.institution_id.astype(int)

# institution -> IPEDS unitids, per year
links = g[["year", "inst", "unitid"]].dropna().drop_duplicates()
links["unitid"] = links.unitid.astype(int)

# GSS counts per institution-year
pre = g[g.year <= 2016].groupby(["year", "inst"]).n.sum().rename("c907").reset_index()
post = g[g.year >= 2017].pivot_table(index=["year", "inst"], columns="gss_code", values="n",
                                    aggfunc="sum").fillna(0).reset_index()

cyears = sorted(c.year.unique())
FIELDS = ["polisci", "ir", "policy", "pubadmin"]


def weights(k_ma, k_dr, lead, span):
    """Completion-based weights per (year t, inst, field), using completion years t+lead .. t+lead+span-1
    (nearest available years when IPEDS has a gap or the window runs past the last IPEDS year)."""
    cc = c.assign(w=np.where(c.level == "ma", k_ma, k_dr) * c.n)
    cw = cc.groupby(["unitid", "year", "field"]).w.sum().unstack("field", fill_value=0)
    cw = cw.reindex(columns=FIELDS, fill_value=0)
    rows = []
    for t in range(1972, 2026):
        want = [t + lead + k for k in range(span)]
        use = sorted({min(cyears, key=lambda y: (abs(y - w), -y)) for w in want})
        sub = cw.loc[cw.index.get_level_values("year").isin(use)].groupby("unitid").sum()
        sub["year"] = t
        rows.append(sub.reset_index())
    w = pd.concat(rows)
    w = links.merge(w, on=["year", "unitid"], how="left").fillna(0)
    return w.groupby(["year", "inst"])[FIELDS].sum().reset_index()


def allocate(df, total_col, w, fields):
    m = df.merge(w, on=["year", "inst"], how="left").fillna(0)
    s = m[fields].sum(axis=1)
    # institutions with no completions in these fields: use that year's pooled shares
    pooled = m.groupby("year")[fields].sum()
    pooled = pooled.div(pooled.sum(axis=1), axis=0)
    sh = m[fields].div(s.replace(0, np.nan), axis=0)
    fb = sh.isna().all(axis=1)
    sh.loc[fb] = pooled.loc[m.loc[fb, "year"]].values
    for f in fields:
        m["est_" + f] = m[total_col] * sh[f]
    m["fallback"] = fb
    return m


def validate(params):
    w = weights(*params)
    v = post.assign(comb=post["907"] + post["912"] + post["914"])
    m = allocate(v, "comb", w, ["polisci", "ir", "policy"])
    agg = m.groupby("year")[["907", "est_polisci", "912", "est_ir", "914", "est_policy"]].sum()
    inst_mae = (m["est_polisci"] - m["907"]).abs().sum() / m["907"].sum()
    agg_err = ((agg.est_polisci - agg["907"]) / agg["907"]).abs().mean()
    return inst_mae, agg_err, agg, m


if __name__ == "__main__":
    grid = [(k_ma, k_dr, lead, span) for k_ma in (1.5, 2) for k_dr in (4, 5, 6)
            for lead in (0, 1) for span in (1, 3, 5)]
    res = []
    for p in grid:
        inst_mae, agg_err, _, _ = validate(p)
        res.append((*p, inst_mae, agg_err))
    res = pd.DataFrame(res, columns=["k_ma", "k_dr", "lead", "span", "inst_abs_err_share", "agg_abs_pct_err"])
    print(res.sort_values("inst_abs_err_share").head(10).to_string(index=False))
    best = tuple(res.sort_values("inst_abs_err_share").iloc[0][["k_ma", "k_dr", "lead", "span"]])
    best = (best[0], best[1], int(best[2]), int(best[3]))
    inst_mae, agg_err, agg, vm = validate(best)
    print("\nbest", best, "\n", agg.round().astype(int).to_string())
    vm.to_csv("output/polisci_validation_2017on_by_institution.csv", index=False)

    # apply to pre-2017
    w = weights(*best)
    m = allocate(pre, "c907", w, FIELDS)
    est = m.groupby("year")[["c907"] + ["est_" + f for f in FIELDS]].sum()
    est["fallback_share"] = m.assign(x=m.c907 * m.fallback).groupby("year").x.sum() / est.c907
    actual = post.groupby("year")[["907", "912", "914"]].sum()
    out = pd.DataFrame({
        "gss_907_combined": est.c907,
        "political_science": est.est_polisci,
        "international_relations": est.est_ir,
        "public_policy": est.est_policy,
        "public_administration": est.est_pubadmin,
        "share_allocated_by_pooled_fallback": est.fallback_share,
    })
    out2 = pd.DataFrame({"political_science": actual["907"], "international_relations": actual["912"],
                         "public_policy": actual["914"]})
    full = pd.concat([out, out2]).sort_index()
    full["source"] = np.where(full.index <= 2016, "estimated (IPEDS split of GSS 907)", "GSS reported")
    full.index.name = "year"
    full.round(3).to_csv("output/polisci_harmonized.csv")
    pd.Series(best, index=["k_ma", "k_dr", "lead", "span"]).to_csv("output/polisci_harmonized_params.csv")
    print(full.round().to_string())
