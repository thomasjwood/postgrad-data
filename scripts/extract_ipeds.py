"""Extract master's and research-doctorate completions in the four fields that made up
GSS code 907 before 2017, by IPEDS UNITID and academic year, from IPEDS Completions files.

  polisci  CIP 45.10  Political science and government
  ir       CIP 45.09  International relations and national security studies
  policy   CIP 44.05  Public policy analysis
  pubadmin CIP 44.04  Public administration

Award levels: 7 = master's; 9 = doctor's (to 2007), 17 = doctor's research/scholarship (2008+).
Year = calendar year in which the academic year ends (C9495 -> 1995, C2016_A -> 2016, C1984 -> 1984).
Usage: python extract_ipeds.py <dir of IPEDS zips> <out.csv>
"""
import os, re, sys, zipfile, io
import pandas as pd

FIELDS = {"45.10": "polisci", "45.09": "ir", "44.05": "policy", "44.04": "pubadmin"}


def year_of(name):
    s = re.sub(r"(?i)^c|_.*|cip$", "", os.path.splitext(name)[0])
    if len(s) == 4 and s[:2] in ("19", "20"):
        return int(s)
    return 1900 + int(s[2:]) if int(s[2:]) > 50 else 2000 + int(s[2:])  # 8990 -> 1990, 9495 -> 1995


# 1980 file uses HEGIS codes (5-digit, e.g. 22070 = HEGIS 2207); no separate public policy code
HEGIS = {"22070": "45.10", "22100": "45.09", "21020": "44.04"}


def norm_cip(c):
    c = str(c).strip().strip('"')
    if c in HEGIS:
        return HEGIS[c]
    if "." not in c:  # numeric 1980s codes: 451001 or 10102
        c = c.zfill(6)
        c = c[:2] + "." + c[2:]
    return c[:5]


out = []
for f in sorted(os.listdir(sys.argv[1])):
    if not f.lower().endswith(".zip"):
        continue
    z = zipfile.ZipFile(os.path.join(sys.argv[1], f))
    csvs = [n for n in z.namelist() if n.lower().endswith(".csv")]
    rv = [n for n in csvs if "_rv" in n.lower()]  # revised release when present
    df = pd.read_csv(io.BytesIO(z.read((rv or csvs)[0])), dtype=str, encoding="latin1")
    # strip a UTF-8 byte-order mark (read as latin1 it shows up as three characters) from the first header
    df.columns = [c.replace("ï»¿", "").replace("﻿", "").strip().strip('"').lower()
                  for c in df.columns]
    if "majornum" in df.columns:
        df = df[df.majornum.astype(str).str.strip() == "1"]
    if year_of(f) == 1980:
        df["cipcode"] = df.cipcode.where(df.cipcode.isin(HEGIS.keys()), "00.0000")
    df["cip"] = df.cipcode.map(norm_cip)
    df = df[df.cip.isin(FIELDS)]
    num = lambda c: pd.to_numeric(df[c], errors="coerce").fillna(0)
    if "ctotalt" in df.columns:
        tot = num("ctotalt")
    else:
        tot = num("crace15") + num("crace16")
    df = df.assign(n=tot, awlevel=pd.to_numeric(df.awlevel, errors="coerce"))
    lvl = df.awlevel.map({7: "ma", 9: "dr", 17: "dr"})
    df = df.assign(level=lvl).dropna(subset=["level"])
    y = year_of(f)
    g = df.groupby(["unitid", "cip", "level"]).n.sum().reset_index()
    g["field"] = g.cip.map(FIELDS)
    g["year"] = y
    out.append(g)
    print(f, y, int(g.n.sum()), g.groupby("field").n.sum().astype(int).to_dict())
pd.concat(out).to_csv(sys.argv[2], index=False)
