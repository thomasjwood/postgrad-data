"""Build a harmonized year x discipline table of social science graduate students
from the NSF/NCSES GSS public-use files (aggregated by scripts/aggregate_puf.py).

GSS field codes changed twice:
  1972-2016  901-910 (907 = political science AND public administration/IR/policy;
                      910 = social sciences nec, incl. area studies, criminology, urban)
  2017-2019  901-915 (911 crim. justice, 912 IR, 914 public policy, 915 human development;
                      public administration no longer eligible)
  2020-      901-919 (916 area/ethnic/gender, 917 criminology, 918 urban split out of 910;
                      905 history & phil. of science and 910 merged into 919;
                      human development moved to psychology as 815)
"""
import pandas as pd
import sys

src = sys.argv[1] if len(sys.argv) > 1 else "data/gss_totals_by_year_and_code.csv"
a = pd.read_csv(src, dtype={"gss_code": str, "year": str})
a = a[a.year != "2017a"].reset_index(drop=True)  # 2017old bridge file is broad-field only
a["year"] = a.year.astype(int)
a["total"] = a.pt_tot_all_races_v.fillna(0) + a.ft_tot_all_races_v.fillna(0)
a["code"] = a.gss_code.astype(int)


def social(year, code):
    if year <= 2016:
        return 901 <= code <= 910
    if year <= 2019:
        return 901 <= code <= 915  # incl. 915 human development
    return 901 <= code <= 919


def psych(year, code):
    return 800 <= code <= 899


# harmonized column for each (year, code)
def column(year, code):
    if code == 901: return "Agricultural economics"
    if code == 902: return "Anthropology"
    if code == 903: return "Economics"
    if code == 904: return "Geography"
    if code == 905: return "History & philosophy of science"
    if code == 906: return "Linguistics"
    if code == 907: return "Political science"
    if code == 908: return "Sociology"
    if code == 909: return "Sociology/anthropology (combined)"
    if code == 911: return "Criminal justice"
    if code == 917: return "Criminology"
    if code == 912: return "International relations"
    if code == 914: return "Public policy"
    if code == 915: return "Human development"
    if code == 916: return "Area, ethnic & gender studies"
    if code == 918: return "Urban studies"
    if code in (910, 919): return "Other social sciences"
    raise ValueError((year, code))


rows = []
for (y, c), t in a.groupby(["year", "code"]).total.sum().items():
    if social(y, c):
        rows.append((y, column(y, c), t))
s = pd.DataFrame(rows, columns=["year", "field", "n"])
wide = s.pivot_table(index="year", columns="field", values="n", aggfunc="sum")

order = ["Political science", "International relations", "Public policy",
         "Economics", "Agricultural economics", "Sociology",
         "Sociology/anthropology (combined)", "Anthropology", "Geography",
         "Linguistics", "Criminal justice", "Criminology",
         "Area, ethnic & gender studies", "Urban studies",
         "History & philosophy of science", "Human development",
         "Other social sciences"]
wide = wide[order]
wide["Social sciences, total"] = wide.sum(axis=1)
psy = a[pd.Series([psych(y, c) for y, c in zip(a.year, a.code)])].groupby("year").total.sum()
wide["Psychology"] = psy
wide = wide.round().astype("Int64")

wide.to_csv("output/social_science_grad_students_wide.csv")
s.groupby(["year", "field"]).n.sum().round().astype(int).reset_index() \
    .to_csv("output/social_science_grad_students_long.csv", index=False)

# master's / doctoral split (collected from 2017 on)
md = a[(a.year >= 2017) & pd.Series([social(y, c) for y, c in zip(a.year, a.code)])].copy()
md["masters"] = md.filter(like="ma_").sum(axis=1)
md["doctoral"] = md.filter(like="dr_").sum(axis=1)
md["field"] = [column(y, c) for y, c in zip(md.year, md.code)]
md.groupby(["year", "field"])[["masters", "doctoral"]].sum().round().astype(int) \
    .reset_index().to_csv("output/social_science_masters_doctoral_2017on.csv", index=False)
print(wide.to_string())
